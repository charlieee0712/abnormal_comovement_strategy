# -*- coding: utf-8 -*-
"""E6j B 块（K 分离研究）原生 FALLBACK 账户 + 同资本 + 冲击括号 + 掩码（brief v1.2 §6 / §8；plan §5–§7）。
一个进程 = (段, 母体, 块)；任务单元 = (槽位, 测量) 组内全部 方向 × α（同一 kept 批次）→ H ∈ {1,2,3,5,10,15,20}。
登记门：B 包清单必须存在且 registry sha 一致；后段（2019–2023 / 2024–2026）另须 `registration/record_B_conditions_receipt.json`
三条件全 PASS 且冻结清单 sha 未变（brief §7）。研究坐标：新成员原值（J 缓存 / E6i 缓存）→ pool0 当日 log 市值 OLS（NS）→
方向排名（hi / lo = (−s).rank）；R1 的 T 槽位在母体 S1 内按源口径重中性化（E6i slot_dep_T）；B3-C 用数组 α = α·r。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_slot as SL
import e6j_engine as EN

OUT = os.path.join(J.RES, 'accounts', 'B')
ALPHAS = (0.125, 0.25, 0.5)
HS = EN.HS_B


def gate(pname):
    p = os.path.join(J.RES, 'registration', 'B_package_manifest.json')
    if not os.path.exists(p):
        raise RuntimeError('登记门：B 包未登记')
    m = json.load(open(p))
    for f, s in m['registry_sha256'].items():
        if J.sha_file(os.path.join(J.RES, 'registry', f)) != s:
            raise RuntimeError('登记门：registry/%s 与登记时 sha 不同' % f)
    if pname in J.POST_SEGS:
        rc = os.path.join(J.RES, 'registration', 'record_B_conditions_receipt.json')
        if not os.path.exists(rc):
            raise RuntimeError('后段守卫：记录 B 生效条件未核验')
        r = json.load(open(rc))
        if not (r.get('all_pass') and r.get('frozen_manifest_sha256') == J.sha_file(p)):
            raise RuntimeError('后段守卫：记录 B 条件未全过或冻结清单 sha 已变')


def raw_cells(env, pname, mid, source):
    arr = (SL.e6i_member_raw(pname, mid)[0] if source == 'E6I' else SL.j_member_raw(pname, mid)[0])
    return arr


def ns_cache(env, raw):
    """研究坐标（与 E6i SB.pct_member 同一路径）：(T, Nc) 原值 → pool0 当日 log 市值 OLS（NS）缓存。"""
    import e6f_core as F
    S = env.S
    df = pd.DataFrame(np.full((S.T, S.Nfull), np.nan), index=S.pool0.index, columns=S.pool0.columns)
    df.iloc[:, S.ccols] = raw
    return F.neu_cache(df, S.pool0, S.log_mcap, S.icodes_neu, 'NS')[0]


def pct_of(env, cache, direction):
    import e6g_core as G
    S = env.S
    D = G.pct_dense_dir(cache, S.dates, S.ccolpos, S.Nc, 'hi' if direction == 'high_bad' else 'lo')
    return env.cells_of_dense(D)


def ns_pct(env, raw, direction):
    return pct_of(env, ns_cache(env, raw), direction)


def s1_pct(env, raw, direction):
    """R1 T 槽位：新成员在母体 S1 内按源口径中性化排名（E6i slot_dep_T 同式）。"""
    import e6i_ops as O
    M = env.R.mother('R1')
    z = O._ns_pct_within(env.S, raw, M.s1, 'hi' if direction == 'high_bad' else 'lo')
    return env.cells_of_dense(z)


def run(pname, mother, block):
    t0 = time.time()
    gate(pname)
    rows = pd.read_csv(os.path.join(J.RES, 'registry', 'rows_B.csv'))
    rows = rows[(rows.block == block) & rows.mothers.str.split('|').apply(lambda m: mother in m)]
    if not len(rows):
        return 0
    env = EN.Env(pname, with_prod=False)
    import e6g_c as GC
    mkt = GC.MarketCtx(env.S)
    ci, SE, T = env.ci, env.SE, env.S.T
    log = os.path.join(J.RES, 'logs', 'run_b_%s.log' % pname)
    par = {}
    ids, arrs, summ, masks = [], {k: [] for k in ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss')}, [], {}
    for (slot, mid), grp in rows.groupby(['slot', 'measurement_id'], sort=True):
        st = EN.research_structure(env, mother, slot)
        if slot not in par:                                  # 母体目标（同资本用）
            k0 = st.kept(st.q0[None, :])[0]
            tb, cb = ci.t[k0], ci.c[k0]; wb = SE.dev(tb, cb)
            par[slot] = (k0, tb, cb, wb, np.bincount(tb, weights=wb, minlength=T))
        k0, tb, cb, wb, pb = par[slot]
        src = grp.source.iloc[0]
        Q, labels = [], []
        if block == 'B3C':
            yn = mid.split('_')[-1]
            qm_id, qm_src = ('K_slope20', 'E6I') if yn == 'CC' else ('J_B2_SLOPE20_TR_ID', 'J')
            qM = ns_pct(env, raw_cells(env, pname, qm_id, qm_src), 'low_bad')
            r = env.cells_of_dense(raw_cells(env, pname, mid, 'J'))
            r = np.where(np.isfinite(r), r, 0.0)
            for _, row in grp.iterrows():
                for a in ALPHAS:
                    Q.append(EN.blend(st.q0, [(1.0, qM[None, :])], a * r)[0]); labels.append((row, a))
        else:
            raw = raw_cells(env, pname, mid, src)
            cache = None if (mother == 'R1' and slot == 'T') else ns_cache(env, raw)
            for _, row in grp.iterrows():
                z = s1_pct(env, raw, row.direction) if cache is None else pct_of(env, cache, row.direction)
                for a in ALPHAS:
                    Q.append(EN.blend(st.q0, [(1.0, z[None, :])], a)[0]); labels.append((row, a))
        K = st.kept(np.vstack([q[None, :] for q in Q]))
        for j, (row, a) in enumerate(labels):
            kj = K[j]; t, c = ci.t[kj], ci.c[kj]; w = SE.dev(t, c)
            led = SE.pnl(t, c, w, HS, 8.0)
            pc = np.bincount(t, weights=w, minlength=T); ps = np.minimum(pc, pb)
            with np.errstate(divide='ignore', invalid='ignore'):
                fc = np.where(pc > 0, ps / pc, 0.0); fb = np.where(pb > 0, ps / pb, 0.0)
            scc = SE.pnl(t, c, w * fc[t], HS, 8.0); scb = SE.pnl(tb, cb, wb * fb[tb], HS, 8.0)
            order = np.argsort(t, kind='stable'); ts = t[order]
            bnd = np.searchsorted(ts, np.arange(T + 1))
            idx = [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)]; val = [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
            masks['%s|%s|%s|%s|a=%s' % (row.block, mother, slot, mid, a) + '|' + row.direction] = kj
            for H in HS:
                g, pos, tu, n = led[H]
                br = GC.profile_and_impact(mkt, idx, val, H, full_profile=False)
                did = 'B|%s|%s|%s|%s|%s|FALLBACK|a=%s|H%d' % (row.block, mother, slot, mid, row.direction, a, H)
                ids.append(did)
                for k, v in (('gross', g), ('pos', pos), ('turn', tu), ('net8', n), ('sc_child', scc[H][3]), ('sc_parent', scb[H][3]),
                             ('bracket', br[0]['sqrt']), ('qmiss', br[3])):
                    arrs[k].append(v)
                summ.append(dict(segment=pname, descriptor_id=did, row_id=row.row_id, block=row.block, mother=mother, slot=slot,
                                 measurement_id=mid, direction=row.direction, alpha=a, H=H, net8_ann=float(np.nanmean(n)) * J.ANN,
                                 gross_ann=float(np.nanmean(g)) * J.ANN, turn_mean=float(np.mean(tu)), pos_mean=float(np.mean(pos)),
                                 n_mask_cells=int(kj.sum()), cells_changed_vs_parent=int((kj != k0).sum()),
                                 matched_capital_share=float(ps.sum() / pc.sum()) if pc.sum() > 0 else np.nan))
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    path = os.path.join(od, '%s__%s.npz' % (mother, block))
    J.atomic_write_npz(path, desc=np.array(ids), **{k: np.vstack(v) for k, v in arrs.items()})
    mk = list(masks)
    mpath = os.path.join(od, 'masks_%s__%s.npz' % (mother, block))
    J.atomic_write_npz(mpath, keys=np.array(mk), bits=np.packbits(np.vstack([masks[k][None, :] for k in mk]), axis=1))
    spath = os.path.join(od, 'summary_%s__%s.csv' % (mother, block)); J.atomic_write_csv(spath, pd.DataFrame(summ))
    J.write_receipt('run_b_%s_%s_%s' % (pname, mother, block), [path, mpath, spath], 'SUCCEEDED', n_desc=len(ids),
                    wall_s=round(time.time() - t0, 1), maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0, 2))
    J.log('%s %s %s: %d 描述符 %.0fs' % (pname, mother, block, len(ids), time.time() - t0), log)
    return 0


if __name__ == '__main__':
    a = sys.argv
    sys.exit(run(a[a.index('--segment') + 1], a[a.index('--mother') + 1], a[a.index('--block') + 1]))
