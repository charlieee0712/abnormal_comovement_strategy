#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i M1_CONSENSUS (plan §7.2; A0 路线 M1, 1,512 程序 = 分组 x η{.25,.5,1} x H)。推导段专用。

分组 (A0 编译): 同路线 x 母体 x 估计对象 x 方向 x role(SLOT, FALLBACK) 的 >=2 个成员。每个程序两个账户:
  consensus    成员 bad-score (与该槽位 Stage 2 同源: 均值核 / DEP-K = pool0 NS pct; DEP-T = S1 内重中性化 pct)
               先在同一窗内对各估计形式等权, 再对各窗等权 (nanmean), 当日在域内重排成 pct (average) ->
               SLOT(leg, z_cons, a=η, FALLBACK)。η=1 即完全以共识替代旧腿 (新缺用旧)。
  eqcap_merge  各成员单独 SLOT(leg, z_m, a=η, FALLBACK) 的 DEV 目标权重逐形成日等权平均 (等资本合并目标权重),
               再完整重跑持仓 / 成本 (plan §6.3 "家族组合" 行: 不对成员净值做简单平均)。
描述符 id 沿 A0; eqcap_merge 行 = 同 id 加后缀 '|eqcap' (伴随对象, 不计入 A0 登记数)。
输出 accounts/<seg>/M1_<NN>.csv/.npz, 列与 Stage 2 相同 (核心列)。
"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import io
import re
import sys
import time
import argparse
import collections
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I
import e6i_features as FE
import e6i_s1base as SB
import e6i_ops as OP
import e6i_engine as E
import e6i_stage2 as S2
import e6f_core as F

LEG_OF_ROUTE = {'RT': 'T', 'RK': 'K', 'RC': 'C', 'RA': 'K'}


def form_window(mid, cat):
    w = cat.get(mid, {}).get('window')
    try:
        w = int(w)
    except (TypeError, ValueError):
        w = -1
    form = re.sub(r'(\d+)(?=(_|$))', '', mid, count=1) if w >= 0 else mid
    return form, w


def rank_within(z, dom):
    X = np.where(dom & np.isfinite(z), z, np.nan)
    return pd.DataFrame(X).rank(axis=1, pct=True).values


def member_z(S, M, leg, mid, dirn):
    if M.kind == 'dep' and leg == 'T':
        return OP._ns_pct_within(S, SB.raw_member(S, mid), M.s1, 'hi' if dirn == 'high_bad' else 'lo')
    return OP._dirpct(S, mid, dirn)


def slot_mask(S, M, leg, z, a):
    if M.kind == 'dep' and leg == 'T':
        st2 = OP._blend(M.P.score, z, a, 'FALLBACK')
        keep, _, _ = M._keep_dep(stage2=st2, s1=M.s1)
        return keep & ~M.veto_drop()
    return M.slot(leg, lambda: z, a, 'FALLBACK')[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--shard', type=int, default=0)
    ap.add_argument('--nshard', type=int, default=1)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    assert a.segment in I.DERIV_SEGS or I.post_allowed(a.segment)   # Stage 3 技术修复: 后段需 E6i 记录 B
    t0 = time.time()
    FE.build_catalog()
    FE.CATALOG_IDS = {m['member_id'] for m in FE.CATALOG}
    cat = {m['member_id']: m for m in FE.CATALOG}
    I.set_protected_members(FE.protected_ids())
    dd = pd.read_csv(os.path.join(I.RES, 'registry', 'descriptors_A0.csv'), low_memory=False)
    dd = dd[dd.route_id == 'M1']
    groups = collections.OrderedDict()
    for r in dd.to_dict('records'):
        k = (r['m1_route'], r['mother_id'], r['m1_estimand'], r['direction'], r['member_id'], str(r['strength']))
        groups.setdefault(k, []).append(r)
    keys = list(groups)[a.shard::a.nshard]
    if a.limit:
        keys = keys[:a.limit]
    S = I.seg_i(a.segment, warm=False)
    RN = S2.Runner(S)
    print('段就绪 %.0fs; M1 shard %d/%d: %d 程序' % (time.time() - t0, a.shard, a.nshard, len(keys)), flush=True)
    rows, series = [], collections.defaultdict(list)
    zcache = {}
    n_fail = 0
    for gi, k in enumerate(keys):
        route, mn, est, dirn, mems, eta = k
        rs = groups[k]
        ts = time.time()
        members = mems.split('|')
        try:
            I.guard_i(members, ['M1'], segment=a.segment, label_end=str(S.dates[-1].date()), use='trade',
                      where=rs[0]['descriptor_id'])
            M = RN.mother(mn)
            leg = LEG_OF_ROUTE[route]
            eta = float(eta)
            dom = M.s1 if (M.kind == 'dep' and leg == 'T') else S.p0c
            zs = {}
            for m in members:
                ck = (mn, leg, m, dirn)
                if ck not in zcache:
                    zcache[ck] = member_z(S, M, leg, m, dirn)
                zs[m] = zcache[ck]
            byw = collections.defaultdict(list)
            for m in members:
                f_, w_ = form_window(m, cat)
                byw[w_].append(zs[m])
            with np.errstate(all='ignore'):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', RuntimeWarning)
                    per_w = [np.nanmean(np.stack(v), axis=0) for v in byw.values()]
                    cons = np.nanmean(np.stack(per_w), axis=0)
            zc = rank_within(cons, dom)
            m_cons = slot_mask(S, M, leg, zc, eta)
            W_cons = E.dev_weights(S, m_cons)
            Ws = [E.dev_weights(S, slot_mask(S, M, leg, zs[m], eta)) for m in members]
            W_eq = np.mean(np.stack(Ws), axis=0)
            Wp = RN.parent_W[mn]
            for kind, W, mask in (('consensus', W_cons, m_cons), ('eqcap_merge', W_eq, None)):
                for r in rs:
                    H = int(r['H'])
                    g, p, u, n = E.pnl_W(S, W, H, I.COST)
                    gp_, pp_, up_, np_ = RN.ppnl(mn, H)
                    both = np.isfinite(n) & np.isfinite(np_)
                    dn = np.where(both, n - np_, np.nan)
                    did = r['descriptor_id'] + ('' if kind == 'consensus' else '|eqcap')
                    rec = dict(descriptor_id=did, status='SUCCEEDED', route_id='M1', mother_id=mn,
                               member_id=mems, role='M1', strength=eta, policy=kind, direction=dirn,
                               direction_role='consensus', H=H, representative=False, m1_route=route,
                               m1_estimand=est, m1_n_members=len(members), m1_n_windows=len(byw),
                               companion=(kind != 'consensus'),
                               net8_ann=I.ann(n), gross_ann=I.ann(g), net12_ann=I.ann(g - u * I.COST_HI / 1e4),
                               turn_mean=float(np.nanmean(u)), pos_mean=float(np.nanmean(p)),
                               parent_net8_ann=I.ann(np_), d_net8_ann=I.ann(dn),
                               d_gross_ann=I.ann(np.where(both, g - gp_, np.nan)),
                               d_turn=float(np.nanmean(u - up_)), d_pos=float(np.nanmean(p - pp_)),
                               n_changed_cells=int((mask != M.B).sum()) if mask is not None else -1,
                               target_n_mean=float(mask.sum(1).mean()) if mask is not None else np.nan,
                               parent_n_mean=float(M.B.sum(1).mean()))
                    rows.append(rec)
                    series['descriptor_id'].append(did)
                    for nm, arr in (('net8', n), ('gross', g), ('pos', p), ('turn', u), ('dnet8', dn)):
                        series[nm].append(np.asarray(arr, np.float64))
        except Exception as e:
            n_fail += 1
            traceback.print_exc()
            for r in rs:
                rows.append(dict(descriptor_id=r['descriptor_id'], status='FAILED_TECH',
                                 note='%s: %s' % (type(e).__name__, str(e)[:150])))
        if (gi + 1) % 10 == 0:
            print('  %d/%d 程序 %.0fs (末个 %.1fs)' % (gi + 1, len(keys), time.time() - t0, time.time() - ts),
                  flush=True)
    od = os.path.join(I.RES, 'accounts', a.segment)
    tag = 'M1_%02d' % a.shard + ('_timing' if a.limit else '')
    d = pd.DataFrame(rows)
    p_csv = os.path.join(od, tag + '.csv')
    I.atomic_write_csv(p_csv, d)
    outs = [p_csv]
    if series['descriptor_id']:
        buf = io.BytesIO()
        np.savez(buf, descriptor_id=np.asarray(series['descriptor_id']),
                 **{k: np.vstack(v) for k, v in series.items() if k != 'descriptor_id'})
        p_npz = os.path.join(od, tag + '.npz')
        I.atomic_write_bytes(p_npz, buf.getvalue())
        outs.append(p_npz)
    I.write_receipt(os.path.join(I.RES, 'task_status', 'm1_%s_%s.receipt.json' % (a.segment, tag)),
                    'm1:%s:%s' % (a.segment, tag), outs, status='SUCCEEDED' if n_fail == 0 else 'FAILED',
                    n_fail=n_fail, n_programs=len(keys), elapsed_s=round(time.time() - t0, 1))
    print('[%s %s] 程序 %d / 失败 %d; %.0fs' % (a.segment, tag, len(keys), n_fail, time.time() - t0))
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == '__main__':
    main()
