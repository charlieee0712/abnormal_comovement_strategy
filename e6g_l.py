#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 块 L: carried —— 续选缓冲与持有期 (brief §6 / plan §2L) —— 回答 Q8。

L1 形成日续选: U_t = N_t ∪ [I_{t−1} ∩ B^b_t ∩ pool0_t \\ T_t]
  N_t  = 源形成日目标; B^b_t = 放宽 b 个百分点后的【无否决】核心域; T_t = 毒尾; I_{t−1} = 上一形成日名单
  b ∈ {0, 5, 10, 15} 与 relative1.5; 两预算 L-loose (U_t 全体重 DEV) / L-matchN (m_t = |N_t|)
  **b=0 结构上就返回 N_t** (B^0_t = 核心域, 而 N_t = 核心域 \\ 毒尾, 故 I∩B^0∖T ⊆ N_t) —— 逐位锚
L2 持有期: 七原子 + Blend3 在 b0 扫 H ∈ {3,5,7,10,12,15,20,30}
L-X 提前退出需影子账户, 归 part2 (本脚本不做, coverage 记 deferred)
"""
import os, sys, json, time, argparse
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6g_core as G
import e6g_desc as GD
import e6g_c as CC

ATOMS = {'R1': 'KT_dep(50,50)|C:k5', 'R2': 'KT_mean@30|C:k5+cr5:k10',
         'A03': 'KT_dep(50,50)|C:k5+cr5:k10', 'A06': 'KTC_mean@25|cvr_1d:k10+cr5:k10',
         'A07': 'KTC_mean@30|cvr_1d:k10+cr5:k10', 'A08': 'T@30|C:k5+cr5:k10',
         'T25': 'T@25|C:k5+cr5:k10'}
BS = [0, 5, 10, 15, 'relative1.5']
HGRID = [3, 5, 7, 10, 12, 15, 20, 30]


def relaxed_domain(ctx, core, b):
    """B^b_t: 均值/单因子核按原排序放宽 d -> min(100, d+b); DEP 核第一阶段不动,
       只放宽第二阶段保留比例 (b 的单位是【第二阶段百分位点】)。

       b=0 直接用【源 SRC 核心域】而不是 RANKBUDGET@d0 —— brief §6 要求 b=0 精确复现源账本。
       两者在 d0 上的差 (floor(n·d/100) vs qcut) 另有 H0 诊断的 RANKBUDGET_vs_SRC 列登记,
       relaxed 域的 b->0 一致性单独测, 不混进主锚。"""
    S = ctx.S
    if b == 0:
        return ctx.build_core_g(dict(core, sel='SRC', depth=None))
    if core['kind'] in ('single', 'mean'):
        d0 = float(core['s'])
        d = min(100.0, d0 * 1.5) if b == 'relative1.5' else min(100.0, d0 + float(b))
        m, score, cand = ctx.build_core_g(dict(core, sel='RANKBUDGET', depth=d))
        return m, score, cand
    d0 = float(core['b'])
    d = min(100.0, d0 * 1.5) if b == 'relative1.5' else min(100.0, d0 + float(b))
    md = dict(core, sel='RANKBUDGET', depth=d)
    return ctx.build_core_g(md)


def veto_drop(ctx, cfg):
    return ctx.build_veto_drop_g(cfg.get('veto'), cfg['core'])


def buffered_targets(S, Nmask, Bmask, Tdrop, score, budget):
    """逐形成日推进缓冲。返回 (目标掩码, 逐日诊断)。"""
    T, Nc = Nmask.shape
    out = np.zeros((T, Nc), bool)
    I = np.zeros(Nc, bool)
    keep_streak = np.zeros(Nc, int)
    diag = dict(n_new=np.zeros(T, int), n_carried=np.zeros(T, int), n_target=np.zeros(T, int),
                max_streak=0, n_reselect=np.zeros(Nc, int))
    for t in range(T):
        p0 = S.p0c[t]
        elig = I & Bmask[t] & p0 & ~(Tdrop[t] if Tdrop is not None else False)
        U = Nmask[t] | elig
        if budget == 'matchN':
            m = int(Nmask[t].sum())
            if m == 0:
                sel = np.zeros(Nc, bool)               # m_t = 0 -> 不发新目标
            else:
                old = np.flatnonzero(elig)
                if len(old) > m:                       # 旧成员按当日原排序优先留到 m_t
                    o = old[np.argsort(np.where(np.isfinite(score[t, old]),
                                                score[t, old], np.inf))][:m]
                    sel = np.zeros(Nc, bool); sel[o] = True
                else:
                    sel = np.zeros(Nc, bool); sel[old] = True
                    need = m - len(old)
                    fresh = np.flatnonzero(Nmask[t] & ~sel)
                    if need > 0 and len(fresh):
                        f = fresh[np.argsort(np.where(np.isfinite(score[t, fresh]),
                                                      score[t, fresh], np.inf))][:need]
                        sel[f] = True
        else:
            sel = U
        out[t] = sel
        diag['n_target'][t] = int(sel.sum())
        diag['n_new'][t] = int((sel & ~I).sum())
        diag['n_carried'][t] = int((sel & I).sum())
        keep_streak = np.where(sel, keep_streak + 1, 0)
        diag['max_streak'] = max(diag['max_streak'], int(keep_streak.max()) if Nc else 0)
        diag['n_reselect'] += (sel & I).astype(int)
        I = sel
    return out, diag


def ev(S, M, mask, H=K.HOLD, impact=True):
    idx, val = F.dev_from_dense(S, mask)
    g_, p_, tu, n8 = F.sparse_pnl_H(S, idx, val, H, F.COST)
    d = dict(gross_ann=G.ann(g_), net8_ann=G.ann(n8), net12_ann=G.ann(g_ - tu * 12e-4),
             turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
             target_n=float(mask.sum(1).mean()))
    if impact:
        br = CC.profile_and_impact(M, idx, val, H, full_profile=False)[0]
        d['bracket_sqrt_mean'] = float(np.nanmean(br['sqrt']))
        d['bracket_lin_mean'] = float(np.nanmean(br['lin']))
    return d, (g_, p_, tu, n8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    A = ap.parse_args()
    t0 = time.time()
    S = G.seg(A.segment, verbose=False)
    ctx = GD.GCtx(S)
    M = CC.MarketCtx(S)
    out = os.path.join(G.RES, 'L')
    os.makedirs(out, exist_ok=True)
    print('段就绪 %.0fs' % (time.time() - t0), flush=True)

    rows, checks, member_targets = [], [], {}
    for nm, cid in ATOMS.items():
        cfg = GD.parse_cfg(cid)
        Nmask, score, cand, core_mask = ctx.full_mask_g(cfg)
        Tdrop = veto_drop(ctx, cfg)
        base_e = ev(S, M, Nmask)[0]
        rows.append(dict(segment=A.segment, atom=nm, config_id=cid, b='source', budget='source',
                         H=K.HOLD, role='source', **base_e))
        for b in BS:
            Bmask, bscore, _ = relaxed_domain(ctx, cfg['core'], b)
            for budget in ('loose', 'matchN'):
                tg, diag = buffered_targets(S, Nmask, Bmask, Tdrop, score, budget)
                e, dl = ev(S, M, tg)
                r = dict(segment=A.segment, atom=nm, config_id=cid, b=str(b), budget=budget,
                         H=K.HOLD, role='economic',
                         n_new_mean=float(diag['n_new'].mean()),
                         n_carried_mean=float(diag['n_carried'].mean()),
                         max_consecutive_days=int(diag['max_streak']),
                         mean_reselect_per_stock=float(diag['n_reselect'].mean()),
                         cells_vs_source=int((tg != Nmask).sum()), **e)
                rows.append(r)
                if b == 0:
                    checks.append(dict(segment=A.segment, atom=nm, budget=budget,
                                       b0_cells_vs_source=int((tg != Nmask).sum()),
                                       b0_net8_diff=float(e['net8_ann'] - base_e['net8_ann']),
                                       note='b=0 必须逐位等于源 N_t'))
                if b == 0 and budget == 'loose' and nm in G.BLEND3_MEMBERS:
                    member_targets[nm] = tg
                if b == 10 and budget == 'matchN' and nm in G.BLEND3_MEMBERS:
                    member_targets[nm + '_b10'] = tg
        print('  %s 完成 %.0fs' % (nm, time.time() - t0), flush=True)

    # ---- L2 持有期 ----
    for nm, cid in ATOMS.items():
        cfg = GD.parse_cfg(cid)
        Nmask = ctx.full_mask_g(cfg)[0]
        for H in HGRID:
            e, _ = ev(S, M, Nmask, H=H)
            rows.append(dict(segment=A.segment, atom=nm, config_id=cid, b='0', budget='source',
                             H=H, role='horizon', **e))
    # Blend3 的缓冲与持有期
    if len(member_targets) >= 3:
        ivs = [F.dev_from_dense(S, member_targets[m]) for m in G.BLEND3_MEMBERS]
        bi, bv = G.blend3_weights(ivs)
        for H in HGRID:
            g_, p_, tu, n8 = F.sparse_pnl_H(S, bi, bv, H, F.COST)
            rows.append(dict(segment=A.segment, atom='Blend3', config_id='A03+A06+A08 /3',
                             b='0', budget='member_level', H=H,
                             role='horizon' if H != K.HOLD else 'economic',
                             gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                             net12_ann=G.ann(g_ - tu * 12e-4),
                             turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                             target_n=float(np.mean([len(x) for x in bi]))))
        if all((m + '_b10') in member_targets for m in G.BLEND3_MEMBERS):
            ivs2 = [F.dev_from_dense(S, member_targets[m + '_b10']) for m in G.BLEND3_MEMBERS]
            bi2, bv2 = G.blend3_weights(ivs2)
            g_, p_, tu, n8 = F.sparse_pnl_H(S, bi2, bv2, K.HOLD, F.COST)
            rows.append(dict(segment=A.segment, atom='Blend3', config_id='A03+A06+A08 /3',
                             b='10', budget='member_level_matchN', H=K.HOLD, role='economic',
                             gross_ann=G.ann(g_), net8_ann=G.ann(n8),
                             net12_ann=G.ann(g_ - tu * 12e-4),
                             turn_mean=float(np.nanmean(tu)), pos_mean=float(np.nanmean(p_)),
                             target_n=float(np.mean([len(x) for x in bi2]))))

    # ---- 低频刷新参照 (每 {2,3,5} 日形成一次, 所有日历相位) ----
    for nm in ('R2', 'A06', 'A08'):
        cfg = GD.parse_cfg(ATOMS[nm])
        Nmask, score, _, _ = ctx.full_mask_g(cfg)
        Tdrop = veto_drop(ctx, cfg)
        for every in (2, 3, 5):
            for phase in range(every):
                tg = np.zeros_like(Nmask)
                I = np.zeros(S.Nc, bool)
                for t in range(S.T):
                    if t % every == phase:
                        I = Nmask[t].copy()
                    else:
                        I = I & S.p0c[t] & ~(Tdrop[t] if Tdrop is not None else False)
                    tg[t] = I
                e, _ = ev(S, M, tg, impact=False)
                rows.append(dict(segment=A.segment, atom=nm, config_id=ATOMS[nm],
                                 b='lowfreq%d_ph%d' % (every, phase), budget='lowfreq',
                                 H=K.HOLD, role='control_lowfreq', **e))

    pd.DataFrame(rows).to_csv(os.path.join(out, 'L_%s.csv' % A.segment), index=False)
    json.dump(checks, open(os.path.join(out, 'L_checks_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    bad = [c for c in checks if c['b0_cells_vs_source'] != 0]
    json.dump(dict(block='L', segment=A.segment, n_rows=len(rows),
                   b0_anchor_failures=len(bad), elapsed_s=round(time.time() - t0, 1)),
              open(os.path.join(G.RES, 'task_status', 'DONE_L_%s.json' % A.segment), 'w'),
              indent=1, ensure_ascii=False)
    print('DONE L %s: %d 行, b0 锚不符 %d 条, %.0fs'
          % (A.segment, len(rows), len(bad), time.time() - t0), flush=True)


if __name__ == '__main__':
    main()
