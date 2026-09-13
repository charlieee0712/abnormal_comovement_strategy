#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 后段首次观察的补充读数 (brief §7 其余条目)。

e6h_post.py 封存的是段级点估与五道对照; 本脚本补 §7 还要求的:
  - 逐年 / 单年留一 / 相对 R1@H5 与 R2@H5
  - 逐日 NW t (lag 5 / 20)
  - 族同时带: F-route (同 route_id) 与 F-headline (本轮全部后段注册路径),
    stationary bootstrap 2000 draws, 块 20 / 60, 段内, **共同抽样**
  - S0 / S1 / S2 账户 (mu 用 <=2018 冻结估计; **只在记录 B 批准的成员内构造** ——
    全族选择账户被记录 B 这道闸挡住, 已登记为 LIMIT)

守卫照常; 清单 SHA 再核一次。

用法: python3 e6h_post_extra.py --segment 2019-2023 [--draws 2000]
"""
from __future__ import annotations
import os
import sys
import json
import time
import hashlib
import argparse
import collections

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6h_run_routes as RR
import e6h_expand as EX
import e6h_selection as SEL
import e6h_stats as ST
import e6g_core as G
import e6g_desc as GD
import e6f_core as F
import e6e_core as K

RES = H.RES
HS = [3, 5, 10, 20]


def approved_ids():
    p = os.path.join(RES, 'registration', 'record_B_approved.json')
    d = json.load(open(p))
    assert d.get('status') == 'APPROVED'
    chk = dict(d)
    chk.pop('list_sha256', None)
    sha = hashlib.sha256(json.dumps(chk, indent=1, ensure_ascii=False,
                                    sort_keys=True).encode()).hexdigest()
    assert sha == d['list_sha256'], '清单 SHA 与批准时不符'
    ids = set()
    for e in d['entries']:
        ids |= set(e.get('descriptor_ids') or [])
    return d, ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--draws', type=int, default=2000)
    a = ap.parse_args()
    assert a.segment in H.POST_SEGS
    t0 = time.time()
    appr, ids = approved_ids()
    H.load_approval()
    rows = [r for r in EX.all_descriptors() if r['descriptor_id'] in ids]
    assert len(rows) == len(ids)
    S = H.seg(a.segment, verbose=False)
    yrs = pd.DatetimeIndex(S.dates).year.values
    uyr = sorted(set(yrs.tolist()))
    print('  清单 SHA OK; %d 描述符; 段 %d 日, 年 %s' % (len(rows), S.T, uyr), flush=True)

    # 固定参照账户的逐日 net8 (H=5)
    refd = {}
    for nm in ('R1', 'R2'):
        ctxp = GD.GCtx(S)
        m = ctxp.full_mask_g(GD.parse_cfg(G.DISPLAY_ID[nm]))[0]
        ix, vl = F.dev_from_dense(S, m)
        refd[nm] = np.asarray(F.sparse_pnl_H(S, ix, vl, K.HOLD, F.COST)[3], float)

    meta = {}
    out, daily, pctx, ivcache = [], {}, {}, {}
    for i, r in enumerate(rows):
        p = r['parent']
        if p not in pctx:
            pctx[p] = RR.ParentCtx(S, p)
        P = pctx[p]
        keys = [k for k in (r.get('new_key'), r.get('vol_key'), r.get('risk_key'),
                            r.get('liq_key'), r.get('state_key')) if k]
        if r['route_id'] == 'I-P-peer-up-laggard':
            keys += ['IND_CUR_20', 'REL_IND_20']
        H.guard_h(keys, 'trade', segment=a.segment, where=r['descriptor_id'],
                  route_id=r['route_id'], rule_objects=[r['role']])
        mask, wmul, _ = RR.build_mask(P, r)
        idx, val = F.dev_from_dense(S, mask)
        if wmul is not None:
            val = [v * wmul[t, idx[t]] if len(idx[t]) else v for t, v in enumerate(val)]
        isid = bool(r.get('is_identity'))
        if not isid:
            ivcache[r['descriptor_id']] = (idx, val)
        pidx, pval = F.dev_from_dense(S, P.B)
        ctl = None if isid else RR.controls(P, mask)
        for Hh in HS:
            n1 = np.asarray(F.sparse_pnl_H(S, idx, val, Hh, F.COST)[3], float)
            n0 = np.asarray(F.sparse_pnl_H(S, pidx, pval, Hh, F.COST)[3], float)
            dn = np.where(np.isfinite(n1) & np.isfinite(n0), n1 - n0, np.nan)
            key = (r['descriptor_id'], Hh)
            daily[key] = dn
            meta[key] = dict(route_id=r['route_id'], is_identity=isid)
            m_, t5, n_ = ST.nw_t(dn, 5)
            _, t20, _ = ST.nw_t(dn, 20)
            rec = dict(segment=a.segment, descriptor_id=r['descriptor_id'],
                       route_id=r['route_id'], parent=p, role=r['role'], H=Hh,
                       is_identity=isid, new_key=r.get('new_key'),
                       alpha=r.get('alpha'), w=r.get('w'), q=r.get('q'), eta=r.get('eta'),
                       d_net8_ann=H.ann(dn), nw_t_lag5=t5, nw_t_lag20=t20,
                       n_days=int(np.isfinite(dn).sum()))
            for y in uyr:
                rec['y%d' % y] = H.ann(np.where(yrs == y, dn, np.nan))
            loo = [H.ann(np.where(yrs != y, dn, np.nan)) for y in uyr]
            rec['loyo_min'] = float(np.nanmin(loo))
            rec['loyo_max'] = float(np.nanmax(loo))
            rec['loyo_worst_year'] = int(uyr[int(np.nanargmin(loo))])
            if Hh == K.HOLD:
                rec['d_vs_R1_H5'] = H.ann(np.where(np.isfinite(n1), n1 - refd['R1'], np.nan))
                rec['d_vs_R2_H5'] = H.ann(np.where(np.isfinite(n1), n1 - refd['R2'], np.nan))
                if ctl is not None:
                    for cn, cp in ctl.items():
                        cd = np.where(np.isfinite(n1), n1 - np.asarray(cp[3], float), np.nan)
                        rec['d_vs_%s' % cn] = H.ann(cd)
            out.append(rec)
        if (i + 1) % 20 == 0:
            print('    %d/%d  %.0fs' % (i + 1, len(rows), time.time() - t0), flush=True)

    od = os.path.join(RES, 'post_segments')
    os.makedirs(od, exist_ok=True)
    d = pd.DataFrame(out)
    d.to_csv(os.path.join(od, 'post_extra_%s.csv' % a.segment), index=False)
    print('  逐年/留一/NW 完成 %d 行, %.0fs' % (len(d), time.time() - t0), flush=True)

    # ---- 族同时带 (共同抽样) ----
    mem = [k for k in daily if not meta[k]['is_identity']]
    fams = {'F-headline': mem}
    for rid in sorted(set(r['route_id'] for r in rows)):
        fams['F-route|%s' % rid] = [k for k in mem if meta[k]['route_id'] == rid]
    band_rows = []
    M = np.vstack([daily[k] for k in mem])
    mu = np.nanmean(M, axis=1)
    pos = {k: j for j, k in enumerate(mem)}
    ANN = 252 * 100.0
    for block in (20, 60):
        rng = np.random.default_rng(ST.SEED + block)
        BM = np.empty((len(mem), a.draws))
        for b in range(a.draws):
            ix = ST.stationary_idx(S.T, block, rng)      # 共同抽样: 全族同一条下标
            BM[:, b] = np.nanmean(M[:, ix], axis=1)
        se = BM.std(axis=1, ddof=1)
        for fname, ks in fams.items():
            if not ks:
                continue
            jj = [pos[k] for k in ks]
            z = np.abs(BM[jj] - mu[jj][:, None]) / np.maximum(se[jj][:, None], 1e-12)
            crit = float(np.percentile(z.max(axis=0), 95))
            lo = (mu[jj] - crit * se[jj]) * ANN
            hi = (mu[jj] + crit * se[jj]) * ANN
            band_rows.append(dict(segment=a.segment, family=fname, block=block,
                                  n_members=len(ks), draws=a.draws, crit=crit,
                                  n_point_positive=int((mu[jj] > 0).sum()),
                                  n_simul_positive=int((lo > 0).sum()),
                                  n_simul_negative=int((hi < 0).sum()),
                                  median_point_ann=float(np.median(mu[jj]) * ANN),
                                  median_halfwidth_ann=float(np.median(crit * se[jj]) * ANN)))
            print('    [%-34s] block=%d 成员 %3d 点估正 %3d 同时带正 %d 同时带负 %d crit %.2f'
                  % (fname, block, len(ks), int((mu[jj] > 0).sum()), int((lo > 0).sum()),
                     int((hi < 0).sum()), crit), flush=True)
    pd.DataFrame(band_rows).to_csv(
        os.path.join(od, 'post_family_bands_%s.csv' % a.segment), index=False)

    # ---- S0 / S1 / S2 账户 (mu 用 <=2018 冻结估计; 只在已批准成员内) ----
    parents = sorted(set(r['parent'] for r in rows))
    fs = []
    for sg in H.DERIV_SEGS:
        for pp in parents:
            f = os.path.join(RES, 'route_results', 'summary_%s_%s.csv' % (sg, pp))
            if os.path.exists(f):
                fs.append(pd.read_csv(f))
    dv = pd.concat(fs, ignore_index=True)
    fit = dv[dv.descriptor_id.isin(ivcache) & (dv.segment == '2015-2018')]
    mu_of = dict(zip(fit.descriptor_id, fit.d_net8_ann))
    rmap = {r['descriptor_id']: r for r in rows}
    by_dom = collections.defaultdict(list)
    for did in ivcache:
        by_dom[SEL.domain_key(pd.Series(rmap[did]))].append(did)
    sel_rows = []
    for dom, dids0 in sorted(by_dom.items()):
        dids = sorted(x for x in dids0 if x in mu_of)
        if len(dids) < 2:
            continue
        pname = rmap[dids[0]]['parent']
        P = pctx[pname]
        pidx, pval = F.dev_from_dense(S, P.B)
        n0 = np.asarray(F.sparse_pnl_H(S, pidx, pval, K.HOLD, F.COST)[3], float)
        meas = [rmap[x].get('new_key') or rmap[x].get('w') for x in dids]
        mus = np.array([mu_of[x] for x in dids], float)

        def acct(nm, ivs, wts, nmem, member=None):
            mi, mv = SEL.merge_weights(ivs, wts)
            n1 = np.asarray(F.sparse_pnl_H(S, mi, mv, K.HOLD, F.COST)[3], float)
            dn = np.where(np.isfinite(n1) & np.isfinite(n0), n1 - n0, np.nan)
            _, t5, _ = ST.nw_t(dn, 5)
            sel_rows.append(dict(segment=a.segment, domain=dom, account=nm,
                                 n_members=nmem, member=member,
                                 d_net8_ann=H.ann(dn), net8_ann=H.ann(n1),
                                 parent_net8_ann=H.ann(n0), nw_t_lag5=t5))

        s0 = dids[int(np.argmax(mus))]
        acct('S0', [ivcache[s0]], [1.0], 1, member=s0)
        w1 = SEL.hierarchical_weights([rmap[x] for x in dids], 'new_key')
        acct('S1', [ivcache[x] for x in dids], list(w1), len(dids))
        for tau in (0.5, 1.0, 2.0):
            w0, wc = SEL.s2_weights(mus, meas, pi0=0.5, tau=tau)
            acct('S2_tau%g' % tau, [(pidx, pval)] + [ivcache[x] for x in dids],
                 [w0] + list(wc), len(dids))
    sd = pd.DataFrame(sel_rows)
    sd.to_csv(os.path.join(od, 'post_selection_%s.csv' % a.segment), index=False)
    print('  S0/S1/S2 账户 %d 行 (%d 个域)'
          % (len(sd), sd.domain.nunique() if len(sd) else 0))
    if len(sd):
        print(sd.groupby('account').d_net8_ann.agg(['count', 'mean', 'median']).round(3).to_string())
    print('  [%s] 补充读数完成, %.0fs' % (a.segment, time.time() - t0))


if __name__ == '__main__':
    main()
