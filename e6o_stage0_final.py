# -*- coding: utf-8 -*-
"""E6o Stage 0 终版引擎刷新（B 之后）：
  python3 e6o_stage0_final.py pre    快照 A1 时表（引擎 v1）→ *_preA2.csv（只在不存在时写）
  （链中随后重跑 e6o_stage0.py / e6o_stage0b.py：恒等、攻击样例、S0-5 试跑计数用终版引擎 v3 重算）
  python3 e6o_stage0_final.py post   合并：S0-11 资源行保留 A2 前估计（写进 note），加实测墙钟行；比对数据事实行（应逐字相同）
A2 / B 的经济读数不读 stage0 任何行；本步只刷新工程恒等与计数。"""
import os
import sys
import json
import glob
import shutil

import pandas as pd

import e6o_core as O

SNAP = [('diagnostics', 'stage0_E6o.csv'), ('verify', 'identities_E6o_stage0.csv'), ('diagnostics', 'stage0_accounting_bridge_E6o.csv'),
        ('diagnostics', 'S0_10_age_remaining_E6o.csv')]
ENGINE_PROBES = ('S0-2', 'S0-5', 'S0-7', 'S0-8', 'S0-10', 'S0-11')


def snap(d, f):
    return O.P(d, f.replace('.csv', '_preA2.csv'))


def pre():
    for d, f in SNAP:
        if not os.path.exists(snap(d, f)):
            shutil.copy2(O.P(d, f), snap(d, f))
    print('snapshot ok')


def post():
    new = pd.read_csv(O.P('diagnostics', 'stage0_E6o.csv'), keep_default_na=False, dtype=str)
    old = pd.read_csv(snap('diagnostics', 'stage0_E6o.csv'), keep_default_na=False, dtype=str)
    ok_ = old.set_index(['probe_id', 'key'])
    changed = []
    for i, r in new.iterrows():
        k = (r.probe_id, r.key)
        if k not in ok_.index:
            continue
        ov = str(ok_.loc[k, 'value'])
        if ov != str(r.value):
            if r.probe_id in ENGINE_PROBES:
                new.loc[i, 'note'] = (str(r.note) + '；' if r.note else '') + 'A2 前（引擎 v1）值 = %s' % ov
            else:
                changed.append('%s|%s' % k)
    recs = {}
    for p in glob.glob(O.P('task_status', '*.receipt.json')):
        j = json.load(open(p))
        recs[j.get('task_id', '')] = j
    add = [dict(probe_id='S0-11', item='Stage 0 终版引擎刷新', key='ENGINE_REFRESH', value='v3', unit='count', status='INFO', source_file='e6o_stage0_final.py',
                note='恒等 / 攻击样例 / S0-5 计数于 B 后用终版引擎（v3：卖出整批分配修正）重算；A2 前原表存 diagnostics/stage0_E6o_preA2.csv、verify/identities_E6o_stage0_preA2.csv')]
    for tid, key in (('E6o_accounts_A2', 'ACTUAL_WALL_S_ACCOUNTS_A2'), ('E6o_accounts_B', 'ACTUAL_WALL_S_ACCOUNTS_B'), ('E6o_randoms_A2', 'ACTUAL_WALL_S_RANDOMS_A2'),
                     ('E6o_randoms_B', 'ACTUAL_WALL_S_RANDOMS_B'), ('E6o_randoms_B_topup', 'ACTUAL_WALL_S_RANDOMS_TOPUP')):
        if tid in recs:
            add.append(dict(probe_id='S0-11', item='实测墙钟 %s' % tid, key=key, value=recs[tid].get('wall_s', ''), unit='count', status='INFO',
                            source_file='task_status/%s.receipt.json' % tid, note='秒；峰值 RSS %s GB' % recs[tid].get('rss_peak_gb', '')))
    new = new[~new.key.isin([a['key'] for a in add])]
    new = pd.concat([new, pd.DataFrame(add)], ignore_index=True)
    order = {('S0-%d' % i): i for i in range(14)}
    new = new.assign(_o=new.probe_id.map(order)).sort_values('_o', kind='stable').drop(columns='_o')
    O.atomic_write_csv(O.P('diagnostics', 'stage0_E6o.csv'), new)
    print(json.dumps(dict(rows=len(new), data_fact_rows_changed=changed[:20], n_changed=len(changed)), ensure_ascii=False), flush=True)
    if changed:
        sys.exit(1)


if __name__ == '__main__':
    pre() if sys.argv[1] == 'pre' else post()
