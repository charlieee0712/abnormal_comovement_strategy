# -*- coding: utf-8 -*-
"""E6m 附属清单覆盖状态（registry/auxiliary_manifest_E6m.csv 全部 66,698 行；附录 D-5"coverage registered == computed"）。
每一行的状态都从实际产物推出（只读账户 / 随机分片里的 ID 列表与名单层 facts 的状态列，不读任何数值）：
  item 1 DETERMINISTIC_ACCOUNT  owner 在本阶段各段账户（accounts / accounts_aux）里都有 → COMPUTED；否则取名单层状态（SOURCE_WAIT 等）或 NOT_RUN
         MATCH_CAP_FIXED_PATH   同上（sc_child 与主账户同表产出）
  item 2–4 随机                 （owner, H）在本阶段各段 randoms/<机制>/ 分片里、路径 ≥ 1,024 → COMPUTED；未排 / 无新内容 → 各自状态词；否则 NOT_RUN
  item 5 / 6 附属名单 / 账户     masks_aux facts 状态（COMPUTED / SOURCE_WAIT / DEFINITION_PENDING / ACCOUNT_STAGE）；ACCOUNT_STAGE 再看 accounts_aux facts
  item 7 状态链                 SOURCE_THEORY 两种初始化 → 连续面板（e6m_s_continuous）里该 aux_id 本阶段各段都 COMPUTED 则 COMPUTED，否则 NOT_RUN；
                                FULL_FILL_SAME_MODEL / SOURCE_LIMIT_SHADOW → LIMIT（源模型不具备撮合细节，plan §7 第 7 项；limit_register L-S1）
输出 <out>/aux_status_E6m_<phase>.csv（逐行）与 aux_status_summary_<phase>.csv（item × kind × 状态计数）。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M


def segs_of(phase):
    return tuple(M.DERIV_SEGS) if phase == 'deriv' else tuple(M.SEGMENTS)


def acc_ids(root, seg):
    ids = set()
    for d in ('accounts', 'accounts_aux'):
        for f in glob.glob(os.path.join(root, d, seg, '*.npz')):
            z = np.load(f, allow_pickle=False)
            ids |= set(str(x) for x in z['desc'])
    return ids


def rand_paths(root, seg):
    out = {}
    for f in glob.glob(os.path.join(root, 'randoms', '*', seg, '*.npz')):
        mech = os.path.basename(os.path.dirname(os.path.dirname(f)))
        z = np.load(f, allow_pickle=False)
        seen = set()
        for i, (d, H) in enumerate(zip([str(x) for x in z['desc']], z['H'])):
            k = (mech, d, int(H))
            if k in seen:                  # 同分片内重复登记行只计一次（2026-10-11）
                continue
            seen.add(k)
            out[k] = out.get(k, 0) + int(z['n_net'].shape[1])           # 本分片的路径数（路径区间互不重叠）
    return out


def aux_facts(root, seg):
    st = {}
    for d in ('masks_aux', 'accounts_aux'):
        for f in glob.glob(os.path.join(root, d, seg, 'facts_aux*.csv')):
            F = M.read_csv_keep(f, dtype=str)
            for k, s in zip(F.aux_key, F.status):
                st[k.split('|')[0]] = s if d == 'accounts_aux' or k.split('|')[0] not in st else st[k.split('|')[0]]
    sup = {}
    for d in ('masks_aux', 'accounts_aux'):     # 补丁十九：补充件 S1（supp/S1/，不改封存件）只补主路径没有的键；与主路径重键即停
        for f in glob.glob(os.path.join(root, 'supp', 'S1', d, seg, 'facts_aux*.csv')):
            F = M.read_csv_keep(f, dtype=str)
            for k, s in zip(F.aux_key, F.status):
                kk = k.split('|')[0]
                if kk in st:
                    raise RuntimeError('补充件 S1 与主路径重键：%s（%s）' % (kk, seg))
                sup[kk] = s if d == 'accounts_aux' or kk not in sup else sup[kk]
    st.update(sup)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--phase', required=True, choices=['deriv', 'full'])
    ap.add_argument('--root', default='', help='产物根（默认工作目录；开发测试指向 stageS_dev 下的合成目录）')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    t0 = time.time()
    root = a.root or M.work()
    segs = segs_of(a.phase)
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    ids = {s: acc_ids(root, s) for s in segs}
    rp = {s: rand_paths(root, s) for s in segs}
    af = {s: aux_facts(root, s) for s in segs}
    pc = os.path.join(root, 'results', 'full', 'continuous', 'continuous_panel_E6m.csv')
    cont = set()                                      # 连续面板里本阶段各段都 COMPUTED 的 aux_id（e6m_s_continuous ledger：一行 = owner × 段，含 carry / reset 两种初始化）
    if os.path.exists(pc):
        Pc = M.read_csv_keep(pc, dtype=str)
        ok_ = Pc[(Pc.status == 'COMPUTED') & Pc.segment.isin(segs)].groupby('aux_id').segment.nunique()
        cont = set(ok_[ok_ == len(segs)].index)
    out = []
    for r in A.itertuples():
        own = r.owner_id.split('@')[0]
        H = int(r.H)
        if r.item == '1':
            key = own if own.count('|') >= 8 else ('SUPP:' + own[5:21] if own.startswith('SUPP:') else own)
            ok = all(key in ids[s] for s in segs)
            st = 'COMPUTED' if ok else 'NOT_RUN'
        elif r.item in ('2', '3', '4'):
            if r.mechanism == 'NO_NEW_CONTENT_TO_PERMUTE':
                st = 'NO_NEW_CONTENT_TO_PERMUTE'
            else:
                n = [rp[s].get((r.mechanism, own, H), 0) for s in segs]
                st = 'COMPUTED' if all(x >= 1024 for x in n) else ('NOT_RUN' if not any(n) else 'PARTIAL_PATHS')
                if st == 'NOT_RUN' and r.mechanism in ('CONTENT_ISK_P5', 'LEGACY_POLICY_RANDOM') and own.split('|')[2:3] in (['DELETE_HIGH'], ['DELETE_LOW']) \
                        and all(rp[s].get(('DELETE_BUDGET_COND', own, H), 0) >= 1024 for s in segs):
                    st = 'RANDOM_NOT_SCHEDULED'   # V 的内容随机由 DELETE_BUDGET_COND 给出（plan 第 604 行；同 owner × H 已算满；2026-10-11 用户经 advisor 定）
        elif r.item in ('5', '6'):
            vals = [af[s].get(r.aux_id, 'NOT_RUN') for s in segs]
            if all(v == 'COMPUTED' for v in vals):
                st = 'COMPUTED'
            else:
                st = next(v for v in vals if v != 'COMPUTED')
        elif r.item == '7':
            st = ('COMPUTED' if r.aux_id in cont else 'NOT_RUN') if r.mechanism.endswith('SOURCE_THEORY') else 'LIMIT'
        else:
            st = 'UNDEFINED'
        out.append(dict(aux_id=r.aux_id, item=r.item, aux_kind=r.aux_kind, mechanism=r.mechanism, owner_id=r.owner_id, H=H, status=st))
    df = pd.DataFrame(out)
    os.makedirs(a.out, exist_ok=True)
    p1 = os.path.join(a.out, 'aux_status_E6m_%s.csv' % a.phase)
    M.atomic_write_csv(p1, df)
    S = df.groupby(['item', 'aux_kind', 'status']).size().reset_index(name='rows')
    p2 = os.path.join(a.out, 'aux_status_summary_%s.csv' % a.phase)
    M.atomic_write_csv(p2, S)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_aux_status_%s' % a.phase), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__],
                    counts=df.status.value_counts().to_dict(), wall_s=round(time.time() - t0, 1),
                    v_content_by_delete=int(((df.status == 'RANDOM_NOT_SCHEDULED') & df.mechanism.isin(['CONTENT_ISK_P5', 'LEGACY_POLICY_RANDOM'])).sum()))
    print(S.to_string(index=False), flush=True)
    print(json.dumps(dict(rows=len(df), status=df.status.value_counts().to_dict()), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
