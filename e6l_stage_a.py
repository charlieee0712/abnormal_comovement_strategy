# -*- coding: utf-8 -*-
"""E6l Stage A（brief §1.4；附录 B / C；plan §8.1 / §5.2 / §5.5）：推导两段掩码层事实，任何收益读取之前落盘。只读 masks/（名单位图 + 目标层统计）、
mfacts（门层记忆 / 库存 / 测量事实）与段环境（pool0 / 门域 / 行业 / size）；不读任何账户收益。
输出 results/stage_a/：
  mask_facts_deriv_E6l.csv   每目标 × 段：E6k 同口径（n_edits_in / out、edit_weight_share、size_edit_gap_T / LAG1（×100，带符号）、size_port_delta_T / LAG1、
                             small30_share_delta、size_unknown_weight、total_edit_cells、same_ticker_overlap_with_native、edit_persistence_5d_reversal_share）
                             + E6l：自身编辑数（相对本对象昨日名单）、名单日留存率、门层记忆事实（bonus 依靠份额 / 连续依靠日数 / 重确认年龄 / 门留存）、
                             INV 标记覆盖 / 饱和、待到期重合比例（INV）、第二关 / 否决后存活（最终人数 / 门名额）、pool spell 年龄、
                             与 NATIVE / Q0 同算子 / Q0 HG10 的换入重叠、KERNEL_DOSE 状态计数、flags（预冻结回退 / 不适用标注）
  measure_facts_deriv_E6l.csv  每测量 × 母体 × 段：有效数份额、坏度有限份额、RANK 延伸覆盖、共同支持份额、回退域（K 有效而新测量缺失）
  rmark_partition_deriv_E6l.csv  R-MARK ISK 分区：每母体 × 段逐日叶数 / 叶 ≥ 2 的单元份额（分位）
  state_days_deriv_E6l.csv   Vol3 / Act3 三分位日数、UNKNOWN 日数（主 / STRICT250）、Trend3 三态单元份额
  calibration_deriv_E6l.csv  附录 C：PORT3_T 紧区间 lo / hi 与 mid（段均）在 C1 / Q 平滑族 / 旧 K 规则上的分位 50 / 90 / 95；lv5（母体 / 子）
  a2_7_vs_e6k_deriv.csv      附录 A2-7：E6k mask_facts_deriv_E6k 的同构目标 = 本表（1e−9）
回执 task_status/stage_a_masks。"""
import e6l_boot  # noqa: F401
import os
import sys
import glob
import json
import time

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_registry as RG

E6K_FIELDS = ('n_edits_in', 'edit_weight_share', 'edit_persistence_5d_reversal_share', 'size_edit_gap_T', 'size_port_delta_T')


def e6k_target(tid):
    """E6l 目标 ID → E6k 目标 ID（同构者；否则 None）。"""
    p = tid.split('|')
    if p[0] in ('KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL'):
        return None
    f, m, a, op = p[0], p[1], p[2], p[3]
    if f == 'K0':
        if op == 'NATIVE':
            return 'K0|%s|a0|PARENT' % m
        if op in ('HG5', 'HG10', 'HG15'):
            return 'K0|%s|a0|HG_ONLY%s' % (m, op[2:])
        return None
    if f not in ('Q0', 'C1', 'S', 'M'):
        return None
    fk = 'Q' if f == 'Q0' else f
    if op == 'NATIVE':
        return '%s|%s|%s|NATIVE' % (fk, m, a)
    if op in ('HG5', 'HG10', 'HG15'):
        return '%s|%s|%s|NATIVE_%s' % (fk, m, a, op)
    return None


def seg_facts(pname):
    import e6l_env as V
    import e6k_random as RN
    seg = V.SegL(pname)
    ci = seg.ci
    T, Nc, n = seg.T, seg.Nc, seg.n
    t_of, c_of = ci.t, ci.c
    bits, stats = {}, {}
    for f in sorted(glob.glob(L.P('masks', pname, '*.npz'))):
        z = L.npz(f)
        for j, tid in enumerate(map(str, z['targets'])):
            bits[tid] = z['bits'][j]
            stats[tid] = {k[2:]: z[k][j] for k in z if k.startswith('t_')}
    mf = pd.concat([L.read_csv_keep(f) for f in glob.glob(L.P('masks', pname, 'mfacts_*.csv'))], ignore_index=True)
    mf = mf.drop_duplicates('target_id').set_index('target_id')
    cache = {}

    def mask(tid):
        if tid not in cache:
            cache[tid] = np.unpackbits(bits[tid])[:n].astype(bool)
        return cache[tid]
    # pool0 spell 年龄（按列：当前连续在 pool0 的天数，含当日）
    p0 = np.zeros((T, Nc), bool)
    p0[t_of, c_of] = True
    spell = np.zeros((T, Nc), np.int32)
    run = np.zeros(Nc, np.int32)
    for d in range(T):
        run = np.where(p0[d], run + 1, 0)
        spell[d] = run
    spell_c = spell[t_of, c_of]
    rows = []
    for tid in sorted(stats):
        parts = tid.split('|')
        tag = parts[0] if parts[0] in ('KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL') else ''
        body = parts[1:] if tag else parts
        if tag == 'ICL':
            f, p, a, op, Hs = body[0], body[1], body[2], body[4], body[3]
        else:
            f, p, a, op = body[0], body[1], body[2], body[3]
        par = 'K0|%s|a0|NATIVE' % p
        if par not in bits:
            continue
        st = stats[tid]
        m, mp = mask(tid), mask(par)
        ent, ext = m & ~mp, mp & ~m
        r = dict(segment=pname, target_id=tid, variant=tag or 'REGISTERED', meas=f, mother=p, alpha=a, op=op,
                 n_edits_in=float(np.nanmean(st['n_in'])) if np.isfinite(st['n_in']).any() else np.nan,
                 n_edits_out=float(np.nanmean(st['n_out'])) if np.isfinite(st['n_out']).any() else np.nan,
                 edit_weight_share=float(np.nanmean(st['edit_w_in'])) if np.isfinite(st['edit_w_in']).any() else np.nan,
                 size_edit_gap_T=float(np.nanmean(st['gapT']) * 100) if np.isfinite(st['gapT']).any() else np.nan,
                 size_edit_gap_LAG1=float(np.nanmean(st['gapL']) * 100) if np.isfinite(st['gapL']).any() else np.nan,
                 size_edit_gap_abs_T=float(np.nanmean(np.abs(st['gapT'])) * 100) if np.isfinite(st['gapT']).any() else np.nan,
                 size_port_delta_T=float(np.nanmean(0.5 * (st['szT_lo'] + st['szT_hi']))) if np.isfinite(st['szT_lo']).any() else np.nan,
                 size_port_delta_LAG1=float(np.nanmean(0.5 * (st['szL_lo'] + st['szL_hi']))) if np.isfinite(st['szL_lo']).any() else np.nan,
                 size_port_lo_T_segavg=float(np.nanmean(st['szT_lo'])) if np.isfinite(st['szT_lo']).any() else np.nan,
                 size_port_hi_T_segavg=float(np.nanmean(st['szT_hi'])) if np.isfinite(st['szT_hi']).any() else np.nan,
                 small30_share_delta=float(np.nanmean(st['small30']) - np.nanmean(stats[par]['small30'])),
                 size_unknown_weight=float(np.nanmean(st['unkT'])), total_edit_cells=int(ent.sum() + ext.sum()),
                 lv5_mean=float(np.nanmean(st['lv5'])), nnames_mean=float(np.nanmean(st['nnames'])))
        nat = '%s|%s|%s|NATIVE' % (f, p, a)
        if op != 'NATIVE' and not tag and nat in bits:
            en = mask(nat) & ~mp
            r['same_ticker_overlap_with_native'] = float((ent & en).sum() / max(ent.sum(), 1))
        for lab, other in (('q0_same_op', 'Q0|%s|%s|%s' % (p, a, op)), ('q0_hg10', 'Q0|%s|%s|HG10' % (p, a))):
            if other in bits and other != tid:
                eo = mask(other) & ~mp
                r['overlap_in_%s' % lab] = float((ent & eo).sum() / max((ent | eo).sum(), 1))
        ii = np.flatnonzero(ent)
        dense = np.zeros((T, Nc), bool)
        dense[t_of[m], c_of[m]] = True
        if len(ii):
            gone = 0
            samp = ii[:: max(1, len(ii) // 2000)]
            for k in samp:
                t0, c0 = t_of[k], c_of[k]
                win = dense[t0 + 1:min(T, t0 + 6), c0]
                gone += int(len(win) and not win.all())
            r['edit_persistence_5d_reversal_share'] = gone / len(samp)
            mature = samp[t_of[samp] + 5 < T]
            r['edit_5d_mature_events'] = int(len(mature))
            r['edit_5d_immature_events'] = int(len(samp) - len(mature))
        # 自身编辑（相对本对象昨日名单）与日留存
        nd = dense.sum(1)
        keepd = (dense[1:] & dense[:-1]).sum(1)
        prevn = nd[:-1]
        live = prevn > 0
        r['self_edits_per_day'] = float(np.mean((nd[1:] - keepd)[live] + (prevn - keepd)[live])) if live.any() else np.nan
        r['list_retention'] = float(keepd[live].sum() / prevn[live].sum()) if live.any() else np.nan
        # 第二关 / 否决后存活（最终人数 / 门名额；门名额 = dom.K[d]）
        st_ = seg.struct(p)
        K = st_.dom.K.astype(float)
        fin = np.bincount(t_of[m], minlength=T)
        ok = K > 0
        r['downstream_survival'] = float(fin[ok].sum() / K[ok].sum()) if ok.any() else np.nan
        r['pool_spell_age_mean'] = float(spell_c[m].mean()) if m.any() else np.nan
        if op == 'INV10':
            H = int((Hs if tag == 'ICL' else parts[-1])[1:])
            pend = []
            for d in range(H, T):
                if nd[d]:
                    pend.append((dense[d] & dense[d - H]).sum() / nd[d])
            r['inv_H'] = H
            r['pending_expiry_overlap'] = float(np.mean(pend)) if pend else np.nan
        if tid in mf.index:
            fa = mf.loc[tid]
            for k in ('bonus_reliant_share', 'reliant_run_p50', 'reliant_run_p90', 'reliant_run_max', 'confirm_age_p50', 'confirm_age_p90', 'confirm_age_max',
                      'gate_retention', 'inv_mark_coverage', 'inv_saturated_day_share', 'cells_vs_parent', 'cells_vs_native', 'cap_zero_days_loop', 'kd_status'):
                if k in fa.index and str(fa[k]) not in ('', 'nan'):
                    r[k] = fa[k]
        flags = []
        if r['total_edit_cells'] == 0 and not (f == 'K0' and op == 'NATIVE'):
            flags.append('NO_EDITS_EQUIV_PARENT')
        if op == 'INV10' and float(r.get('inv_saturated_day_share', 0) or 0) > 0:
            flags.append('INV_SATURATED_DAYS')
        r['flags'] = '|'.join(flags) if flags else 'NONE'
        rows.append(r)
    F = pd.DataFrame(rows)
    # 测量事实
    mrows = []
    meas_cols = [c for c in mf.columns if c.startswith('meas_')]
    if meas_cols:
        mm = mf.reset_index()
        mm['meas'] = mm.target_id.str.split('|').str[0]
        mm['mother'] = mm.target_id.str.split('|').str[1]
        mm = mm[~mm.meas.isin(['KD', 'CSC', 'CSP', 'MQ0', 'S250', 'ICL'])]
        g = mm.groupby(['meas', 'mother'])[meas_cols].first().reset_index()
        g.insert(0, 'segment', pname)
        mrows.append(g)
    for p in V.E.P6:
        st_ = seg.struct(p)
        k0 = st_.q0
        for meas in V.QALL + ('C1', 'S', 'M'):
            kf = seg.meas_kf(meas)
            base = np.isfinite(k0)
            mrows.append(pd.DataFrame([dict(segment=pname, meas=meas, mother=p, fallback_k0_valid_meas_missing=float((base & ~np.isfinite(kf)).sum() / max(base.sum(), 1)))]))
    M = pd.concat(mrows, ignore_index=True) if mrows else pd.DataFrame()
    # R-MARK 分区
    rp = []
    for p in V.E.P6:
        st_ = seg.struct(p)
        valid = np.zeros(n, bool)
        valid[st_.ids] = True
        leaf, stats_ = RN.tree_leaves(seg, valid, st_.q0, 'ISK')
        lv = leaf[st_.ids]
        cnt = np.bincount(lv)
        nl, mov = [], []
        for d in range(T):
            a0, b0 = st_.dom.off[d], st_.dom.off[d + 1]
            if b0 == a0:
                continue
            u = np.unique(lv[a0:b0])
            nl.append(len(u))
            mov.append(float((cnt[lv[a0:b0]] >= 2).mean()))
        rp.append(dict(segment=pname, mother=p, leaves_per_day_p10=float(np.percentile(nl, 10)), leaves_per_day_p50=float(np.percentile(nl, 50)),
                       leaves_per_day_p90=float(np.percentile(nl, 90)), movable_cell_share_p10=float(np.percentile(mov, 10)),
                       movable_cell_share_p50=float(np.percentile(mov, 50)), tree=json.dumps(stats_)))
    # 状态日数
    sd = []
    stv = seg.st
    for var, key, keyS in (('Vol3', 'vol_state', 'vol_state_strict'), ('Act3', 'act_state', 'act_state_strict')):
        for defn, k in (('MAIN_GE150', key), ('STRICT250', keyS)):
            x = np.asarray(stv[k])
            sd.append(dict(segment=pname, variable=var, definition=defn, unknown_days=int((x < 0).sum()), low_days=int((x == 0).sum()),
                           mid_days=int((x == 1).sum()), high_days=int((x == 2).sum())))
    tr = seg.trend_cells
    sd.append(dict(segment=pname, variable='Trend3', definition='ENDPOINT_MA20_GE16（pool0 单元份额）', unknown_days=float((tr < 0).mean()),
                   low_days=float((tr == 0).mean()), mid_days=float((tr == 1).mean()), high_days=float((tr == 2).mean())))
    return F, M, pd.DataFrame(rp), pd.DataFrame(sd)


def main():
    t0 = time.time()
    post = '--post' in sys.argv                                # 后段掩码事实：授权条件 + seal_post 之后（沿 E6k mask_facts_post）
    tag = 'post' if post else 'deriv'
    segs = L.POST_SEGS if post else L.DERIV_SEGS
    od = L.P('results', 'stage_a')
    os.makedirs(od, exist_ok=True)
    if post:
        import e6l_seal as SEAL
        ok_, bad_ = SEAL.verify('post')
        if not ok_:
            raise RuntimeError('seal_post 核对失败：%s' % bad_[:5])
    Fs, Ms, Rs, Ss = [], [], [], []
    for s in segs:
        if post:
            L.post_gate(s, 'Stage A 后段掩码事实')
        else:
            L.deriv_only(s, 'Stage A')
        F, M, Rp, Sd = seg_facts(s)
        Fs.append(F)
        Ms.append(M)
        Rs.append(Rp)
        Ss.append(Sd)
        print('%s：%d 目标事实' % (s, len(F)), flush=True)
    F = pd.concat(Fs, ignore_index=True)
    M = pd.concat(Ms, ignore_index=True)
    Rp = pd.concat(Rs, ignore_index=True)
    Sd = pd.concat(Ss, ignore_index=True)
    # 附录 C 校准（推导两段；紧区间与 lv5 来自目标层统计，不读收益）
    cal = []
    reg = F[F.variant == 'REGISTERED'].copy()
    groups = {'C1': reg.meas == 'C1', 'Q_SMOOTH': reg.meas.str.startswith('Q_'), 'Q0': reg.meas == 'Q0', 'OLD_RULE_K0': (reg.meas == 'K0') & (reg.op != 'NATIVE')}
    for s in segs:
        for gname, gm in groups.items():
            x = reg[gm & (reg.segment == s)]
            for col in ('size_port_lo_T_segavg', 'size_port_hi_T_segavg', 'size_port_delta_T', 'lv5_mean'):
                v = x[col].astype(float).values
                v = v[np.isfinite(v)]
                if len(v):
                    cal.append(dict(segment=s, group=gname, column=col, n_targets=len(v), p50=float(np.percentile(v, 50)), p90=float(np.percentile(v, 90)),
                                    p95=float(np.percentile(v, 95)), share_outside_pm3_pct_pt=float(np.mean(np.abs(v) > 3.0)) if 'size_port' in col else np.nan))
    par = reg[(reg.meas == 'K0') & (reg.op == 'NATIVE')]
    for s in segs:
        v = par[par.segment == s].lv5_mean.astype(float).values
        cal.append(dict(segment=s, group='PARENT', column='lv5_mean', n_targets=len(v), p50=float(np.median(v)), p90=float(np.percentile(v, 90)),
                        p95=float(np.percentile(v, 95)), share_outside_pm3_pct_pt=np.nan))
    Cal = pd.DataFrame(cal)
    # A2-7
    ek = pd.read_csv(L.K6('registry', 'mask_facts_%s_E6k.csv' % tag), keep_default_na=False, na_values=[''])
    ek = ek.set_index(['segment', 'target_id'])
    chk = []
    for r in reg.itertuples():
        et = e6k_target(r.target_id)
        if et is None or (r.segment, et) not in ek.index:
            continue
        e = ek.loc[(r.segment, et)]
        for k in E6K_FIELDS:
            a_, b_ = getattr(r, k, np.nan), e[k] if k in e.index else np.nan
            a_, b_ = float(a_), float(b_)
            same = (np.isnan(a_) and np.isnan(b_)) or (np.isfinite(a_) and np.isfinite(b_) and abs(a_ - b_) <= 1e-9)
            chk.append(dict(segment=r.segment, target_id=r.target_id, e6k_target=et, field=k, e6l=a_, e6k=b_, status='PASS' if same else 'FAIL'))
    A27 = pd.DataFrame(chk)
    outs = []
    for nm, df in (('mask_facts_%s_E6l.csv' % tag, F), ('measure_facts_%s_E6l.csv' % tag, M), ('rmark_partition_%s_E6l.csv' % tag, Rp),
                   ('state_days_%s_E6l.csv' % tag, Sd), ('calibration_%s_E6l.csv' % tag, Cal), ('a2_7_vs_e6k_%s.csv' % tag, A27)):
        p = os.path.join(od, nm)
        L.atomic_write_csv(p, df)
        outs.append(p)
    ok = len(A27) > 0 and not (A27.status == 'FAIL').any()
    L.write_receipt('stage_a_masks' + ('_post' if post else ''), outs, 'SUCCEEDED' if ok else 'FAILED', rows=len(F), a2_7=A27.status.value_counts().to_dict() if len(A27) else {},
                    a2_7_targets=int(A27.target_id.nunique()) if len(A27) else 0, flags=F['flags'].str.split('|').explode().value_counts().to_dict(),
                    wall_s=round(time.time() - t0, 1))
    print('A2-7：%s（%d 目标）' % (A27.status.value_counts().to_dict() if len(A27) else {}, A27.target_id.nunique() if len(A27) else 0), flush=True)
    print(A27[A27.status == 'FAIL'].head(10).to_string() if len(A27) else '', flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
