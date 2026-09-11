#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 H3: 条件否决 (brief §5 / plan §2H3) —— 回答 Q5。

母体 R2/A06/A08; 焦点 z ∈ {cr5:k10, cvr_1d:k10}。
Q = 移除【同公式同窗口】焦点规则后的母体; 条件策略 = Q_t \\ (T_z,t ∩ S_t)。
锚: S=全集 -> 无条件焦点否决 (= 母体); S=空集 -> Q。
五个状态: K 的 NS 分、T 的 NS 分、log 市值、realized_vol_20d 的 NS 分
(前四项池内 rank(average,pct) >= 0.5 分层, 边界归高侧) + I11 age ∈ {1} vs {2-5}。
对照: Tox-matchN / Core-matchN / Random-state。随机: 128 独立日 + 128 五日持续 (hash 版)。

循环次序: (状态, 侧, 路径) 在外, (母体, 焦点) 在内 —— 状态重排与母体无关, 只算一次。
"""
import os, sys, json, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6g_core as G
import e6g_desc as GD
import e6g_c as CC

PARENTS = {'R2': 'KT_mean@30|C:k5+cr5:k10',
           'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10',
           'A08': 'T@30|C:k5+cr5:k10'}
FOCUS = {'cr5': (GD.spec_of_key(K.FCR5), 10), 'cvr_1d': (GD.spec_of_key(K.FCVR1), 10)}
STATES = ('K_ns', 'T_ns', 'logmcap', 'rvol_ns', 'age1')
M1 = np.uint64(0x9E3779B97F4A7C15)
M2 = np.uint64(0xBF58476D1CE4E5B9)
M3 = np.uint64(0x94D049BB133111EB)


def q_veto(parent_id, focus):
    vn = parent_id.split('|')[1] if '|' in parent_id else ''
    return '+'.join([x for x in vn.split('+') if x and not x.startswith(focus + ':')])


def hkey(seed, tkey, cols):
    x = (np.uint64(seed + 1) * M1 + np.uint64(tkey + 1) * M2 + cols.astype(np.uint64) * M3)
    x ^= x >> np.uint64(30); x *= M2
    x ^= x >> np.uint64(27); x *= M3
    x ^= x >> np.uint64(31)
    return x


def shuffle_state(S, sel, seed, kind):
    """同日同行业内重排状态标签。indep: hash(seed,t,stock); persist: hash(seed,t//5,stock)。
       每天两次 lexsort, 全向量化。"""
    out = np.zeros_like(sel)
    for t in range(S.T):
        v = np.flatnonzero(S.p0c[t])
        if len(v) < 2:
            continue
        ic = S.icodes[t, v]
        kk = hkey(seed, t if kind == 'indep' else t // 5, v)
        o1 = np.lexsort((np.arange(len(v)), ic))      # 行业内按原序
        o2 = np.lexsort((kk, ic))                     # 行业内按 hash 序
        out[t, v[o2]] = sel[t, v[o1]]
    return out


def build_states(S, ctx):
    out, miss = {}, {}

    def from_pct(P):
        st = np.zeros(P.shape, bool)
        mi = np.zeros(P.shape, bool)
        for t in range(S.T):
            v = S.p0c[t] & np.isfinite(P[t])
            mi[t] = S.p0c[t] & ~np.isfinite(P[t])
            if v.sum() >= 2:
                r = pd.Series(P[t, v]).rank(pct=True).to_numpy()
                st[t, np.flatnonzero(v)] = r >= 0.5
        return st, mi

    out['K_ns'], miss['K_ns'] = from_pct(ctx.leg_pct(GD.spec_of_key(K.FK)))
    out['T_ns'], miss['T_ns'] = from_pct(ctx.leg_pct(GD.spec_of_key(K.FT)))
    out['rvol_ns'], miss['rvol_ns'] = from_pct(ctx.leg_pct(G.specF('realized_vol_20d')))
    lm = S.log_mcap.reindex(index=S.pool0.index, columns=S.pool0.columns).values[:, S.ccols]
    out['logmcap'], miss['logmcap'] = from_pct(np.where(np.isfinite(lm), lm, np.nan))
    from pool_screening_v2 import define_i11_signal
    from event_study import get_base_pool
    sg = define_i11_signal(S.feats, get_base_pool(S.data)).reindex(
        index=S.pool0.index, columns=S.pool0.columns).fillna(0).values[:, S.ccols]
    age = np.zeros(sg.shape, np.int8)
    for lag in range(5, 0, -1):
        sh = np.zeros_like(sg); sh[lag:] = sg[:-lag]
        age = np.where(sh > 0, lag, age)
    out['age1'] = (age == 1)
    miss['age1'] = S.p0c & (age == 0)
    return out, miss


def ev(S, M, mask, impact=True):
    idx, val = F.dev_from_dense(S, mask)
    g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, K.HOLD, F.COST)
    d = dict(gross_ann=G.ann(g_), net8_ann=G.ann(n8), net12_ann=G.ann(g_ - tu * 12e-4),
             turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
             target_n=float(mask.sum(1).mean()))
    if impact:
        br = CC.profile_and_impact(M, idx, val, K.HOLD, full_profile=False)[0]
        d['bracket_sqrt_mean'] = float(np.nanmean(br['sqrt']))
        d['bracket_lin_mean'] = float(np.nanmean(br['lin']))
    return d, (g_, p_, tu, n8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--npath', type=int, default=128)
    A = ap.parse_args()
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    M = CC.MarketCtx(S)
    out = os.path.join(G.RES, 'H3')
    os.makedirs(out, exist_ok=True)
    print('段就绪 %.0fs T=%d Nc=%d' % (time.time() - t0, S.T, S.Nc), flush=True)

    ST, MISS = build_states(S, ctx)
    print('状态就绪 %.0fs 高侧占比 %s' % (
        time.time() - t0, {k: round(float(ST[k][S.p0c].mean()), 3) for k in ST}), flush=True)

    # 六个 (母体, 焦点) 的 Q / T_z / 核末级分, 一次算好
    CELL = {}
    rows, checks = [], []
    for pname, pid in PARENTS.items():
        for fz, (spz, kz) in FOCUS.items():
            qv = q_veto(pid, fz)
            qcfg = GD.parse_cfg(pid.split('|')[0] + ('|' + qv if qv else ''))
            Qmask, qscore, _, _ = ctx.full_mask_g(qcfg)
            Pz = ctx.leg_pct(spz)
            Tz = F.drop_mask_dense(Pz, S.p0c, kz)                 # 池级排序
            CELL[(pname, fz)] = (Qmask, qscore, Pz, Tz, qv, pid)
            pm = ctx.full_mask_g(GD.parse_cfg(pid))[0]
            checks.append(dict(parent=pname, focus=fz, q_veto=qv or '(无)',
                               pool_rank_vs_Q_rank_diff_cells=int(
                                   ((Tz & Qmask) != F.drop_mask_dense(Pz, Qmask, kz)).sum()),
                               anchor_S_all_vs_parent_diff=int(((Qmask & ~Tz) != pm).sum()),
                               note='排序恒等: 池级与 Q 内不同, 本块一律用池级'))
            base = dict(parent=pname, parent_cfg=pid, focus=fz, q_veto=qv or '(无)')
            d, _ = ev(S, M, Qmask & ~Tz)
            rows.append(dict(base, state='__ALL__', side='-', role='anchor_S_all', **d))
            d, _ = ev(S, M, Qmask)
            rows.append(dict(base, state='__NONE__', side='-', role='anchor_S_empty', **d))
    print('六个 (母体,焦点) 就绪 %.0fs' % (time.time() - t0), flush=True)

    # ---- 经济格 + 两个确定性对照 ----
    for stname in STATES:
        for side in ('high', 'low'):
            selbase = (ST[stname] if side == 'high' else ~ST[stname]) | MISS[stname]
            for (pname, fz), (Qmask, qscore, Pz, Tz, qv, pid) in CELL.items():
                base = dict(parent=pname, parent_cfg=pid, focus=fz, q_veto=qv or '(无)',
                            state=stname, side=side)
                m = Qmask & ~(Tz & selbase)
                d, _ = ev(S, M, m)
                rows.append(dict(base, role='economic',
                                 n_removed=int((Qmask & Tz & selbase).sum()),
                                 n_removed_uncond=int((Qmask & Tz).sum()),
                                 n_fallback_missing=int((Qmask & Tz & MISS[stname]).sum()), **d))
                tn = (Qmask & Tz & selbase).sum(axis=1).astype(int)
                mt = F.coretrim_matchN(S, -Pz, Qmask & Tz, tn)
                rows.append(dict(base, role='ctl_Tox_matchN',
                                 **ev(S, M, Qmask & ~mt, impact=False)[0]))
                mc = F.coretrim_matchN(S, -qscore, Qmask, tn)
                rows.append(dict(base, role='ctl_Core_matchN',
                                 **ev(S, M, Qmask & ~mc, impact=False)[0]))
        print('  状态 %s 完成 %.0fs' % (stname, time.time() - t0), flush=True)

    # ---- A06 两焦点的四种共同开关 ----
    core_only = ctx.full_mask_g(GD.parse_cfg('KTC_mean@25'))[0]
    Tc = F.drop_mask_dense(ctx.leg_pct(FOCUS['cvr_1d'][0]), S.p0c, 10)
    Tb = F.drop_mask_dense(ctx.leg_pct(FOCUS['cr5'][0]), S.p0c, 10)
    for stname in STATES:
        Sv = ST[stname] | MISS[stname]
        for mode in ('only_v1', 'only_B', 'both', 'neither'):
            dc = (Tc & Sv) if mode in ('only_v1', 'both') else Tc
            db = (Tb & Sv) if mode in ('only_B', 'both') else Tb
            rows.append(dict(parent='A06', parent_cfg=PARENTS['A06'], focus='joint',
                             q_veto='-', state=stname, side=mode, role='joint_switch',
                             **ev(S, M, core_only & ~(dc | db), impact=False)[0]))

    pd.DataFrame(rows).to_csv(os.path.join(out, 'H3_configs_%s.csv' % A.segment), index=False)
    print('确定性部分完成 %.0fs, %d 行; 开始 %d x 2 条随机路径'
          % (time.time() - t0, len(rows), A.npath), flush=True)

    # ---- Random-state: 每 (状态, 侧, kind, seed) 只重排一次, 六个母体共用 ----
    paths, exemplars = [], {}
    for stname in STATES:
        for side in ('high', 'low'):
            selbase = (ST[stname] if side == 'high' else ~ST[stname]) | MISS[stname]
            for kind in ('indep', 'persist'):
                acc = {c: [] for c in CELL}
                for b in range(A.npath):
                    selp = shuffle_state(S, selbase, b, kind)
                    for c, (Qmask, qscore, Pz, Tz, qv, pid) in CELL.items():
                        d, dl = ev(S, M, Qmask & ~(Tz & selp))
                        acc[c].append(d)
                        if b < 4 and c == ('A06', 'cvr_1d'):
                            exemplars['%s|%s|%s|%d' % (stname, side, kind, b)] = dl[3]
                for c, lst in acc.items():
                    arr = {k2: np.array([x[k2] for x in lst]) for k2 in lst[0]}
                    r = dict(parent=c[0], focus=c[1], state=stname, side=side, kind=kind,
                             n_path=A.npath)
                    for k2, v in arr.items():
                        r[k2 + '_mean'] = float(v.mean())
                        r[k2 + '_sd'] = float(v.std(ddof=1))
                        r[k2 + '_mcse'] = float(v.std(ddof=1) / np.sqrt(len(v)))
                    paths.append(r)
                print('  随机 %s/%s/%s 完成 %.0fs' % (stname, side, kind, time.time() - t0),
                      flush=True)

    pd.DataFrame(paths).to_csv(os.path.join(out, 'H3_random_%s.csv' % A.segment), index=False)
    json.dump(checks, open(os.path.join(out, 'H3_checks_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    if exemplars:
        pd.DataFrame(exemplars, index=pd.DatetimeIndex(S.dates)).to_parquet(
            os.path.join(out, 'H3_exemplar_net8_%s.parquet' % A.segment))
    st = dict(block='H3', segment=A.segment, n_config_rows=len(rows), n_path_rows=len(paths),
              npath=A.npath, n_exemplar=len(exemplars), elapsed_s=round(time.time() - t0, 1))
    json.dump(st, open(os.path.join(G.RES, 'task_status', 'DONE_H3_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    print('DONE H3 %s: %d 配置行 %d 路径行 %.0fs'
          % (A.segment, len(rows), len(paths), st['elapsed_s']), flush=True)


if __name__ == '__main__':
    main()
