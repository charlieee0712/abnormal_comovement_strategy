#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 记录 B: 把用户批准的后段清单冻结成机器可读文件 (brief §6)。

**这个文件一旦写下, 守卫就会放行清单内的 route_id 进 2019+。**
所以它把批准的来源、时间、草稿 SHA、以及【精确到描述符 ID 的清单】全部记下来,
并对清单本身算 SHA256 —— 之后跑后段时再核一次, 防止清单在批准后被改。

清单按 registration/record_B_draft.md 的三条, 逐条过滤到描述符级:
  E6H-B-01-MT    M-T x {TCV_20, turnover_5d} (排除 TCV_60) x A06/A08/R2/T25
  E6H-B-02-IPUP  I-P-peer-up x ADD (排除 SWAP) x w=20 (排除 w=5) x R1/R2 (排除 A06)
  E6H-B-03-REF   八个固定参照账户 (旧规则旧输入, 守卫本来就放行, 列出只为 receipt 完整)
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_expand as EX
import e6g_l as L6

RES = H.RES

MT_PARENTS = {'A06', 'A08', 'R2', 'T25'}
MT_KEYS = {'TCV_20', 'turnover_5d'}
IP_PARENTS = {'R1', 'R2'}


def build_list():
    rows = EX.all_descriptors()
    mt, ip = [], []
    for r in rows:
        if r['route_id'] == 'M-T-tcv-vs-t60' and r['parent'] in MT_PARENTS:
            if r.get('is_identity') or r.get('new_key') in MT_KEYS:
                mt.append(r['descriptor_id'])
        elif (r['route_id'] == 'I-P-peer-up-laggard' and r['parent'] in IP_PARENTS
              and r.get('role') == 'ADD'):
            if r.get('is_identity') or int(r.get('w') or 0) == 20:
                ip.append(r['descriptor_id'])
    return sorted(mt), sorted(ip)


def main():
    p_dir = os.path.join(RES, 'registration')
    os.makedirs(p_dir, exist_ok=True)
    out = os.path.join(p_dir, 'record_B_approved.json')
    if os.path.exists(out):
        raise SystemExit('record_B_approved.json 已存在, 不覆盖 (修订请另起 amendment)')

    mt, ip = build_list()
    refs = sorted(list(L6.ATOMS) + ['Blend3'])
    draft = os.path.join(p_dir, 'record_B_draft.md')
    draft_sha = H.sha_file(draft) if os.path.exists(draft) else None

    entries = [
        dict(id='E6H-B-01-MT', route_id='M-T-tcv-vs-t60',
             need='MEASURE_T_MIXES_LEVEL_AND_INSTABILITY',
             parents=sorted(MT_PARENTS), measurements=sorted(MT_KEYS),
             excluded=dict(measurements=['TCV_60'],
                           reason='推导段 8 个 (母体x段) 格里只有 6 格同号'),
             roles=['SLOT_FALLBACK', 'SLOT_REPLACE'],
             grids=dict(alpha=[0, 0.25, 0.5, 1.0], H=[3, 5, 10, 20]),
             n_descriptors=len(mt), descriptor_ids=mt),
        dict(id='E6H-B-02-IPUP', route_id='I-P-peer-up-laggard',
             need='INDUSTRY_MOVED_STOCK_DID_NOT',
             parents=sorted(IP_PARENTS), measurements=['IND_CUR_20', 'REL_IND_20'],
             excluded=dict(parents=['A06'], roles=['SWAP'], w=[5],
                           reason=('A06 的同人数核心对照全负 (那里的增益只是深度); '
                                   'SWAP 推导段全负且随 eta 恶化; w=5 那支全负')),
             roles=['ADD'], grids=dict(w=[20], q=[0.2, 0.3],
                                       eta=[0, 0.10, 0.25, 0.50], H=[3, 5, 10, 20]),
             n_descriptors=len(ip), descriptor_ids=ip),
        dict(id='E6H-B-03-REF', route_id=None, need='fixed_reference_accounts',
             parents=refs, roles=['source'], grids=dict(H=[3, 5, 10, 20]),
             note='旧规则旧输入, 守卫本来就放行; 列出只为 receipt 完整'),
    ]
    payload = dict(
        round='E6h', record='B', status='APPROVED',
        approved_at=time.strftime('%Y-%m-%d %H:%M:%S'),
        approved_by='user',
        approval_provenance=(
            '用户在看过 registration/record_B_draft.md 之后, 对"要不要现在把记录 B 的'
            '清单定下来跑、改哪条说一声"这一问回答"跑吧"。**按草稿原样批准, 未改任何一条。**'
            '如实记录: 这是对整份草稿的一次性批准, 不是逐条签署。'),
        draft_file='registration/record_B_draft.md', draft_sha256=draft_sha,
        approved_route_ids=['M-T-tcv-vs-t60', 'I-P-peer-up-laggard'],
        not_approved=dict(
            route_ids=['M-C-position-window', 'E-V-quiet-price', 'E-V-surge-price',
                       'E-P-path-conditional-focal', 'R-O-overnight-risk',
                       'I-P-peer-down-risk', 'L-Q-margin-liquidity'],
            reason=('推导段已被三道对照否掉; 放进后段只会抬高 F-headline 的多重性分母, '
                    '反而让两个候选更难被看见。逐条理由在草稿里')),
        entries=entries,
        train_cutoff='2018-12-31', label_end_cutoff=H.MARKET_DATA_END_MAX,
        post_segments=list(H.POST_SEGS),
        execution_rule=('两后段按同一清单【全部计算并封存】, 完成 receipt 后共同展示; '
                        '**不看 2019-2023 之后再改 2024-2026**'),
        boundary=('这【不是 OOS】: 路线是在看过 E6g 与 R0 之后选的, 2019+ 的母体本身'
                  '早被看过多次, 研究者知道这两段的 regime。E7 才是唯一 OOS'),
    )
    raw = json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True)
    payload['list_sha256'] = hashlib.sha256(raw.encode()).hexdigest()
    with open(out, 'w') as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)

    print('== 记录 B 已冻结 ==')
    print(' 批准时间 %s' % payload['approved_at'])
    print(' 草稿 SHA %s' % (draft_sha[:16] if draft_sha else 'NA'))
    print(' 清单 SHA %s' % payload['list_sha256'][:16])
    for e in entries:
        print('  %-14s route=%-22s 母体=%-22s 描述符 %s'
              % (e['id'], e['route_id'] or '-', ','.join(e['parents'])[:22],
                 e.get('n_descriptors', '(参照)')))
    print(' 未批准的路线: %d 条' % len(payload['not_approved']['route_ids']))
    # 守卫自检
    H.load_approval()
    print()
    print(' 守卫自检:')
    for rid, seg, should in (('M-T-tcv-vs-t60', '2019-2023', True),
                             ('I-P-peer-up-laggard', '2024-2026', True),
                             ('R-O-overnight-risk', '2019-2023', False),
                             ('E-V-quiet-price', '2024-2026', False),
                             (None, '2019-2023', False)):
        ok, why = H.guard_h(['TCV_20'], 'trade', segment=seg, route_id=rid,
                            rule_objects=['SLOT_FALLBACK'], where='selfcheck',
                            strict=False)
        mark = 'OK ' if ok == should else '!! '
        print('   %s%-22s @ %s -> %s (期望 %s)'
              % (mark, rid or '(无 route_id)', seg, '放行' if ok else '拒绝',
                 '放行' if should else '拒绝'))


if __name__ == '__main__':
    main()
