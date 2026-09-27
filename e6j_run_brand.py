# -*- coding: utf-8 -*-
"""E6j B 块随机对照（plan §8.1 / §10.6；brief §6「随机三类」）：每 (段, 母体, 块) 的每个 (槽位, 测量) 组 × 机制 × 路径，
每条路径真实过算子 / DEV / 持仓 / 成本；同一路径的置换同时给两个方向（先置换中性化残差再映射方向：donor 映射共享）与三个 α、七个 H。
机制：IID（R-SCORE-IID = R-MATCH-SRC 匹配条件）、COND（R-COND，行业 × size3 × 旧 K3 不重叠分区，五日优先序）、
EDIT（EDIT-ENTRY：固定真实换出与共同成员，只随机换入，五日优先序）。B3-C：置换 qM（r 固定）；r-shuffle 另作剂量控制。
流式存储（STREAMED_REPLAYABLE）：逐路径 × 描述符的段年化 net8 / gross / turn 与逐年年化 net8（float32），机制 × 描述符的路径均值日序列；
每路径可由稳定哈希键重放。分片 = 路径区间 [path0, path0 + n)。登记门与后段守卫同 e6j_run_b。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_engine as EN
import e6j_random as RND
import e6j_run_b as RB
import e6j_fast as FAST

EN.STAGE2 = FAST.stage2_fast       # 逐位同 IR.dep_stage2_keep（e6j_test_fast.py）
OUT = os.path.join(J.RES, 'randoms', 'B_test' if '--test' in sys.argv else 'B')
ALPHAS = (0.125, 0.25, 0.5)
HS = EN.HS_B
MECHS = ('IID', 'COND', 'EDIT')
BATCH = 32


def donor_map(vals_hi, cell, u):
    """同一 cell 内：u 降序第 k 个 recipient ← vals_hi 降序第 k 个 donor；返回 donor 下标（相对有效格）。"""
    o_u = np.lexsort((-u, cell)); o_v = np.lexsort((-vals_hi, cell))
    don = np.empty(len(vals_hi), dtype=np.int64)
    don[o_u] = o_v
    return don


def run(pname, mother, block, path0=0, n_paths=1024):
    t0 = time.time()
    RB.gate(pname)
    rows = pd.read_csv(os.path.join(J.RES, 'registry', 'rows_B.csv'))
    rows = rows[(rows.block == block) & rows.mothers.str.split('|').apply(lambda m: mother in m)]
    if not len(rows):
        return 0
    env = EN.Env(pname, with_prod=False)
    ci, SE, S, T = env.ci, env.SE, env.S, env.S.T
    years = pd.to_datetime(pd.Index(S.dates).astype(str)).year.values
    yl = sorted(set(years))
    ind = np.asarray(S.icodes)
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    import hashlib
    desc, ann, yr, dsum, dcnt = [], [], [], [], []
    fp = {}                                                  # (机制, 路径) → sha256（按组 → 组合 → H 的固定次序，逐路径账本指纹）
    samp_desc, samp = [], []                                 # 主配置描述符的抽样完整路径（分片前 2 条路径）
    for (slot, mid), grp in rows.groupby(['slot', 'measurement_id'], sort=True):
        st = EN.research_structure(env, mother, slot)
        parent = st.kept(st.q0[None, :])[0]
        legal = ~st.drop
        src = grp.source.iloc[0]
        # 新分量（两个方向同一 donor 映射）
        if block == 'B3C':
            yn = mid.split('_')[-1]
            qm_id, qm_src = ('K_slope20', 'E6I') if yn == 'CC' else ('J_B2_SLOPE20_TR_ID', 'J')
            zc = {'low_bad': RB.ns_pct(env, RB.raw_cells(env, pname, qm_id, qm_src), 'low_bad')}
            zhi = 1.0 - zc['low_bad']                         # 仅作 donor 排序用（与残差同序的单调变换）
            r = env.cells_of_dense(RB.raw_cells(env, pname, mid, 'J')); r = np.where(np.isfinite(r), r, 0.0)
        else:
            raw = RB.raw_cells(env, pname, mid, src)
            if mother == 'R1' and slot == 'T':
                zc = {d: RB.s1_pct(env, raw, d) for d in grp.direction.unique()}
                zhi = RB.s1_pct(env, raw, 'high_bad') if 'high_bad' not in zc else zc['high_bad']
            else:
                cache = RB.ns_cache(env, raw)
                zc = {d: RB.pct_of(env, cache, d) for d in grp.direction.unique()}
                zhi = zc['high_bad'] if 'high_bad' in zc else RB.pct_of(env, cache, 'high_bad')
            r = None
        V = np.isfinite(zhi)
        vt, vc = ci.t[V], ci.c[V]
        # COND 分区（与路径无关）
        Vd = np.zeros((ci.T, ci.Nc), bool); Vd[vt, vc] = True
        oldk = np.full((ci.T, ci.Nc), np.nan); oldk[ci.t, ci.c] = st.q0
        rr_, cc_, cell, _ = RND.cond_cells(Vd, ind, lm, oldk)
        cid = np.full((ci.T, ci.Nc), -1, np.int64); cid[rr_, cc_] = cell
        cond_cell = cid[vt, vc]
        # 真实子（EDIT 用）
        real = {}
        for _, row in grp.iterrows():
            for a in ALPHAS:
                aa = a * r if r is not None else a
                real[(row.direction, a)] = st.kept(EN.blend(st.q0, [(1.0, zc[row.direction][None, :])], aa))[0]
        combos = [(row.direction, a) for _, row in grp.iterrows() for a in ALPHAS]

        def dense_b(b):
            A = np.zeros((ci.T, ci.Nc), bool); A[ci.t[b], ci.c[b]] = True
            return A
        Ld = dense_b(legal)
        k3 = RND.terciles_rowwise(oldk, Ld)                  # 与路径无关，预先算一次
        # 与路径无关的部分先算（e6j_fast；逐位同 donor_map / edit_entry，e6j_test_fast 逐格核对）
        mapper = {'IID': FAST.DonorMapper(zhi[V], vt.astype(np.int64)), 'COND': FAST.DonorMapper(zhi[V], cond_cell)}
        plans = {k: FAST.EditPlan(ci, ind, k3, parent, v, legal) for k, v in real.items()}
        pl0 = plans[combos[0]]                               # 候选（合法 \ 父）对全部组合相同
        nd = len(combos) * len(HS)
        A_ann = np.full((len(MECHS), n_paths, nd, 3), np.nan, np.float32)
        A_yr = np.full((len(MECHS), n_paths, nd, len(yl)), np.nan, np.float32)
        D_sum = np.zeros((len(MECHS), nd, T)); D_cnt = np.zeros((len(MECHS), nd, T), np.int32)
        main_idx = [ci_ for ci_, (d, a) in enumerate(combos) if a == 0.25]
        n_samp = min(2, n_paths)
        S_full = np.full((len(MECHS), n_samp, len(main_idx), T), np.nan)
        for mi, mech in enumerate(MECHS):
            for b0 in range(0, n_paths, BATCH):
                ps = list(range(path0 + b0, path0 + min(b0 + BATCH, n_paths)))
                # 与组合（方向 × α）无关的随机量每路径只算一次（原实现逐组合重算同一结果）
                if mech == 'EDIT':
                    UI = [env.grid.u_cells(RND.path_key('E6j.B', 'EDIT-ENTRY', mother, 'native', 'EDIT', p), pl0.cand_rc[0], pl0.cand_rc[1], 5)
                          for p in ps]
                else:
                    bd = 1 if mech == 'IID' else 5
                    DON = [mapper[mech](env.grid.u_cells(RND.path_key('E6j.B', mid, mother, 'native', mech, p), vt, vc, bd)) for p in ps]
                for ci_, (d, a) in enumerate(combos):
                    aa = a * r if r is not None else a
                    if mech == 'EDIT':
                        K = np.vstack([plans[(d, a)].entry(u)[None, :] for u in UI])
                    else:
                        zd = zc[d][V]
                        Q = []
                        for don in DON:
                            zp = np.full(ci.n, np.nan); zp[V] = zd[don]
                            Q.append(EN.blend(st.q0, [(1.0, zp[None, :])], aa)[0])
                        K = st.kept(np.vstack([q[None, :] for q in Q]))
                    for j, p in enumerate(ps):
                        kj = K[j]; t, c = ci.t[kj], ci.c[kj]; w = SE.dev(t, c)
                        led = SE.pnl(t, c, w, HS, 8.0)
                        h = fp.setdefault((mi, p), hashlib.sha256())
                        for hi, H in enumerate(HS):
                            g, pos, tu, n = led[H]
                            di = ci_ * len(HS) + hi
                            h.update(np.ascontiguousarray(n, dtype='<f8').tobytes())
                            A_ann[mi, p - path0, di] = (np.nanmean(n) * J.ANN, np.nanmean(g) * J.ANN, np.mean(tu))
                            for yi, y in enumerate(yl):
                                m = (years == y) & np.isfinite(n)
                                if m.any():
                                    A_yr[mi, p - path0, di, yi] = np.mean(n[m]) * J.ANN
                            f = np.isfinite(n)
                            D_sum[mi, di] += np.where(f, n, 0.0); D_cnt[mi, di] += f
                            if H == 5 and ci_ in main_idx and (p - path0) < n_samp:
                                S_full[mi, p - path0, main_idx.index(ci_)] = n
        for (d, a) in combos:
            for H in HS:
                desc.append('B|%s|%s|%s|%s|%s|FALLBACK|a=%s|H%d' % (block, mother, slot, mid, d, a, H))
        for ci_ in main_idx:
            d, a = combos[ci_]
            samp_desc.append('B|%s|%s|%s|%s|%s|FALLBACK|a=%s|H5' % (block, mother, slot, mid, d, a))
        ann.append(A_ann); yr.append(A_yr); dsum.append(D_sum); dcnt.append(D_cnt); samp.append(S_full)
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    tag = '%s__%s__p%d_%d' % (mother, block, path0, path0 + n_paths)
    path = os.path.join(od, tag + '.npz')
    fps = np.array([[fp[(mi, p)].hexdigest() for p in range(path0, path0 + n_paths)] for mi in range(len(MECHS))])
    J.atomic_write_npz(path, desc=np.array(desc), mechs=np.array(MECHS), years=np.array(yl), path0=np.array([path0]), n_paths=np.array([n_paths]),
                       ann=np.concatenate(ann, axis=2), yearly=np.concatenate(yr, axis=2),
                       daily_sum=np.concatenate(dsum, axis=1), daily_cnt=np.concatenate(dcnt, axis=1),
                       path_fingerprint=fps, sample_desc=np.array(samp_desc), sample_paths=np.array([path0 + k for k in range(min(2, n_paths))]),
                       sample_net8=np.concatenate(samp, axis=2))
    J.write_receipt(('test_' if '--test' in sys.argv else '') + 'run_brand_%s_%s' % (pname, tag), [path], 'SUCCEEDED', n_desc=len(desc), n_paths=n_paths, path0=path0,
                    generator=RND.GEN_ID, storage='STREAMED_REPLAYABLE（逐路径指纹 + 主配置抽样完整路径 + 日和 / 日计数）',
                    wall_s=round(time.time() - t0, 1))
    J.log('%s %s: %d 描述符 × %d 路径 %.0fs' % (pname, tag, len(desc), n_paths, time.time() - t0), os.path.join(J.RES, 'logs', 'run_brand_%s.log' % pname))
    return 0


if __name__ == '__main__':
    a = sys.argv
    sys.exit(run(a[a.index('--segment') + 1], a[a.index('--mother') + 1], a[a.index('--block') + 1],
                 int(a[a.index('--path0') + 1]) if '--path0' in a else 0, int(a[a.index('--paths') + 1]) if '--paths' in a else 1024))
