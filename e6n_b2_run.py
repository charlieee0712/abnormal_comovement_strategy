# -*- coding: utf-8 -*-
"""E6n B2 账本诊断（plan §8；brief A15、§1.3-12）：冻结源决策下的逐事件剩余收益与订单差分。不生成可部署退出策略、不参与政策、不开账户级闭环。
单位 = 源引擎（e6i_sparse.SparseEngine.pnl）：形成日 f 的批次（DEV 权重 w）在 t ∈ [f+2, f+H+1] 赚 r0[t]（T+1 VWAP 进、T+1+H VWAP 出），
组合日贡献 = (w / den_t)(r0 − bench)，den_t = min(t−1, H)；换手 = ½ Σ|Δact|，费用 = 换手 × 8bp → 每单位 |Δact| 收 4bp（c = 4e−4，不再乘 2）。
事件（e6n_b2 风险集时钟）：首次触发 T ∈ [e0, n−1]（e0 = f+1、n = f+H+1）；a = max(e0+1, T+1)；a ≥ n → NO_EARLY_OPPORTUNITY；
e_early = 首个可卖 ≥ a；e_base = 首个可卖 ≥ n；e_early < e_base 才是实现的早退。
  FIXED_H     基线终点 = 引擎 n（固定 H 合同；早退为反事实，只报"触发后剩余持有贡献"）
  LONGEST_H   基线终点 = e_base（受限卖出可超 H；不让库存消失）；e_base 在数据外 → 右删失，到边界为止
  CASH        早退后至基线终点留现金：Δ_t = −(w/den_t)(r0[c,t] − bench_t)，t ∈ (e_early, 终点]
  NEXT_RANK   触发收盘已知的源排序下一合法未选名（门分数升序、不在当日最终名单、非触发股、合法（CVR / union 基础域）、e_early 可买、
              当日冻结组合未持有、同日未被先前事件占用；JOINT 按 (入场日, ticker, entry_id) 固定顺序分配）同资金片段持有至同一终点
  费用        o_base = 冻结源计划的逐日净订单（act_j − act_{j−1}，act = 有效批次权重 / den）；δo = 该批次提前卖出（j = e_early−1：−w/den）与取消正常卖出
              （j = f+H：+w/den），NEXT 加替代买卖；SOLO：单 entry 相对同一 base 的 c·Σ(|o+δo| − |o|)；JOINT_FROZEN：先合全部 δo 再收费（两者不相加）
  对照（CVR_JUMP）SAME_RATE_RANDOM：同日 × 同持有日龄层按真实触发数从未退出风险集随机抽（64 路径，稳定哈希；不足 → BUDGET_SHORTFALL）；
              CVR_LEVEL_WORST：同层按当日 CVR 水平最差抽同数；BERNOULLI_RISK：过去 60 日（≥ 20 有效日）同日龄触发率伯努利（64 路径；不足 → UNKNOWN）
输出 results/<phase>/b2/：b2_risk_set.csv、b2_events_<段>.npz、b2_order_overlay.csv、b2_mirrors.csv、b2_controls.csv。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_b2 as B2

C_FEE = 4e-4
NPATH = 64


def seg_inputs(seg_name):
    import e6l_env as V
    import e6k_acct as AC
    import e6n_vars as VR
    seg = V.SegL(seg_name, state=False)
    B = VR.Base(seg_name)
    if not (np.array_equal(seg.ci.t, B.t) and np.array_equal(seg.ci.c, B.c)):
        raise RuntimeError('单元坐标不一致')
    z = B2.load_triggers()
    fd = {d: i for i, d in enumerate(z['dates'])}
    fc = {c: j for j, c in enumerate(z['columns'])}
    dates = [str(x)[:4] + '-' + str(x)[4:6] + '-' + str(x)[6:] for x in B.get('dates')]
    codes = [str(x) for x in B.get('codes')]
    ri = np.array([fd[d] for d in dates])
    cj = np.array([fc.get(c, -1) for c in codes])
    if (cj < 0).any():
        raise RuntimeError('触发面板缺列')
    sub = lambda k: np.ascontiguousarray(z[k][np.ix_(ri, cj)])
    P = dict(sell=sub('sell'), buy=sub('buy'), cvr_pct=sub('cvr_pct').astype(float), **{k: sub(k) for k in B2.TRIGS})
    acct = AC.Acct(seg, impact=False)
    return seg, B, P, acct


def batches(seg, B, acct, form, key):
    zm = np.load(N.P('masks', seg.pname, '%s.npz' % form), allow_pickle=False)
    keys = [str(k) for k in zm['mask_keys']]
    F = np.unpackbits(zm['final_bits'][keys.index(key)])[:B.n].astype(bool)
    tg = acct.target(F)
    o = np.lexsort((tg['c'], tg['t']))
    return tg['t'][o].astype(np.int64), tg['c'][o].astype(np.int64), tg['w'][o], tg['ids'][o]


def act_matrix(t, c, w, H, T, Nc):
    """引擎 act_j = (1/den_j) Σ_{k<H} W[j−k]（den_j = min(j+1, H)）→ (T, Nc)。"""
    W = np.zeros((T, Nc))
    np.add.at(W, (t, c), w)
    A = np.cumsum(W, axis=0)
    A[H:] -= A[:-H]
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    return A / den[:, None]


def fee_diff(base_o, deltas):
    """deltas：dict (j, c) → δo；返回 (Σ c·(|o+δo| − |o|) 的逐日序列（按 t = j + 2 记账）, 冲突格数)。"""
    T = base_o.shape[0]
    out = np.zeros(T)
    for (j, c), d in deltas.items():
        if 0 <= j < T:
            o = base_o[j, c]
            tt = j + 2
            if tt < T:
                out[tt] += C_FEE * (abs(o + d) - abs(o))
    return out


def event_rows(t, c, w, H, trig, sell, T, run):
    st, td, ee, eb, uk = run(t, c, trig, sell, H, T)
    return st, td, ee, eb


def cash_series(c, w, e_early, end, r0, bench, T, H):
    """CASH：Δ_t = −(w/den_t)(r0[t,c] − bench_t)，t ∈ (e_early, end]（end 截到 T−1）。返回 (逐日 Δ, 事件 bp, 事件 stock 超额 bp)。"""
    d = np.zeros(T)
    ev = np.zeros(len(c))
    ex = np.zeros(len(c))
    for i in range(len(c)):
        a, b = e_early[i] + 1, min(end[i], T - 1)
        if b < a:
            continue
        tt = np.arange(a, b + 1)
        den = np.minimum(tt - 1, H).astype(float)
        x = r0[tt, c[i]] - bench[tt]
        v = -(w[i] / den) * x
        d[tt] += v
        ev[i] = v.sum() * 1e4
        ex[i] = -x.sum() * 1e4
    return d, ev, ex


def run_seg(seg_name, phase, forms=None):
    import e6l_fast as FA  # noqa: F401
    t0 = time.time()
    seg, B, P, acct = seg_inputs(seg_name)
    SE = seg.SE
    r0 = np.asarray(SE.r0, float)
    bench = np.asarray(SE.bench, float)
    T, Nc = r0.shape
    run = B2.risk_facts_numba()
    rows_ov, rows_mir, rows_ctl, rows_rs = [], [], [], []
    ev_store = {}
    structs = {}
    tagf = "ALL" if not forms else "_".join(forms)
    for form, key in [(f, k) for f, k in B2.OBJECTS if not forms or f in forms]:
        tb, cb, wb, ids = batches(seg, B, acct, form, key)
        if form not in structs:
            structs[form] = seg.struct(form)
        st = structs[form]
        # 门分数（触发日排序用）：对象 K
        k0 = np.asarray(st.q0, float)
        if key.endswith('NATIVE'):
            K = k0
        else:
            K = np.where(np.isfinite(B.kQ), 0.75 * k0 + 0.25 * B.kQ, k0)
        sc = st.gate_scores(K[None, :])[0]
        gid = np.asarray(st.ids, np.int64)
        legal = st.legal()
        Fmask = np.zeros(seg.n, bool)
        Fmask[ids] = True
        for H in B2.HOLDS:
            A = act_matrix(tb, cb, wb, H, T, Nc)
            base_o = np.vstack([A[:1], np.diff(A, axis=0)])
            held = A > 0
            for tg in B2.TRIGS:
                trig = P[tg]
                st_, td, ee, eb = event_rows(tb, cb, wb, H, trig, P['sell'], T, run)
                ent = st_ != B2.NOT_ENTERED
                trg = (st_ != B2.NOT_TRIGGERED) & ent
                real = st_ == B2.REALIZED
                rows_rs.append(dict(segment=seg_name, form=form, object_key=key, trigger=tg, H=H, batches=int(len(tb)), entered=int(ent.sum()),
                                    triggered=int(trg.sum()), realized_early=int(real.sum()), no_early_opportunity=int((st_ == B2.NO_EARLY).sum()),
                                    no_executed_difference=int((st_ == B2.NO_DIFF).sum()), early_unsellable_censored=int((st_ == B2.CENSORED).sum()),
                                    base_right_censored=int((ent & (eb < 0)).sum()), status='COMPUTED'))
                ix = np.flatnonzero(real)
                if not len(ix):
                    for hm in ('FIXED_H', 'LONGEST_H'):
                        for mir in ('CASH', 'NEXT_RANK'):
                            for fee in ('SOLO', 'JOINT_FROZEN'):
                                rows_ov.append(dict(segment=seg_name, form=form, object_key=key, trigger=tg, H=H, horizon_mode=hm, mirror=mir, fee_mode=fee,
                                                    n_events=0, status='NO_REALIZED_EARLY_EXIT'))
                    continue
                f, c, w, e_early = tb[ix], cb[ix], wb[ix], ee[ix]
                n_end = f + H + 1
                for hm in ('FIXED_H', 'LONGEST_H'):
                    end = n_end if hm == 'FIXED_H' else np.where(eb[ix] >= 0, eb[ix], T - 1)
                    cens = (end >= T) | ((hm == 'LONGEST_H') & (eb[ix] < 0))
                    dC, evC, exC = cash_series(c, w, e_early, end, r0, bench, T, H)
                    # NEXT_RANK（JOINT 分配顺序：入场日、ticker、entry_id）
                    used = {}
                    nxt = np.full(len(ix), -1, np.int64)
                    order = np.lexsort((ix, c, f + 1))
                    for i in order:
                        d = int(td[ix[i]])
                        a0, a1 = int(seg.off[d]), int(seg.off[d + 1])
                        cand = np.arange(a0, a1)
                        if not len(gid) or not len(cand):
                            continue
                        pos = np.minimum(np.searchsorted(gid, cand), len(gid) - 1)
                        okc = (gid[pos] == cand) & legal[cand] & ~Fmask[cand]
                        cand, pos = cand[okc], pos[okc]
                        scc = sc[pos]
                        fin = np.isfinite(scc)
                        cand = cand[fin][np.argsort(scc[fin], kind='stable')]
                        eday = int(e_early[i])
                        for cc in cand:
                            col = int(B.c[cc])
                            if col == c[i] or not P['buy'][eday, col] or held[min(eday - 1, T - 1), col] or used.get((eday, col)):
                                continue
                            used[(eday, col)] = True
                            nxt[i] = col
                            break
                    dN = dC.copy()
                    evN = evC.copy()
                    for i in range(len(ix)):
                        if nxt[i] < 0:
                            continue
                        a, b = e_early[i] + 1, min(end[i], T - 1)
                        if b < a:
                            continue
                        tt = np.arange(a, b + 1)
                        den = np.minimum(tt - 1, H).astype(float)
                        v = (w[i] / den) * (r0[tt, nxt[i]] - bench[tt])
                        dN[tt] += v
                        evN[i] += v.sum() * 1e4
                    for mir, dser, evs in (('CASH', dC, evC), ('NEXT_RANK', dN, evN)):
                        # 费用：SOLO（逐 entry 相对同一 base）与 JOINT（合并 δo 后收费）
                        joint = {}
                        solo = np.zeros(len(ix))
                        for i in range(len(ix)):
                            den_e = float(min(max(e_early[i] - 1, 0) + 1, H))
                            dd = {(int(e_early[i]) - 1, int(c[i])): -w[i] / den_e, (int(f[i] + H), int(c[i])): w[i] / H}
                            if mir == 'NEXT_RANK' and nxt[i] >= 0:
                                dd[(int(e_early[i]) - 1, int(nxt[i]))] = dd.get((int(e_early[i]) - 1, int(nxt[i])), 0.0) + w[i] / den_e
                                dd[(int(f[i] + H), int(nxt[i]))] = dd.get((int(f[i] + H), int(nxt[i])), 0.0) - w[i] / H
                            solo[i] = fee_diff(base_o, dd).sum() * 1e4
                            for k_, v_ in dd.items():
                                joint[k_] = joint.get(k_, 0.0) + v_
                        fj = fee_diff(base_o, joint)
                        for fee, fser, fev in (('SOLO', None, solo), ('JOINT_FROZEN', fj, None)):
                            g_ann = float(np.mean(dser)) * N.ANN
                            fee_ann = float(np.mean(fser)) * N.ANN if fser is not None else float(np.sum(solo) / 1e4 / T) * N.ANN
                            rows_ov.append(dict(segment=seg_name, form=form, object_key=key, trigger=tg, H=H, horizon_mode=hm, mirror=mir, fee_mode=fee,
                                                n_events=int(len(ix)), gross_ann_pp=g_ann, fee_delta_ann_pp=fee_ann, net_ann_pp=g_ann - fee_ann,
                                                gross_bp_per_event=float(np.mean(evs)), fee_bp_per_event=float(np.mean(solo)) if fee == 'SOLO' else np.nan,
                                                right_censored_events=int(cens.sum()), next_rank_unfilled=int((nxt < 0).sum()) if mir == 'NEXT_RANK' else 0,
                                                quality='INDUSTRY_CAP_UNCHECKED' if mir == 'NEXT_RANK' else 'OK',
                                                old_proxy_8bp_per_exit_ann_pp=float(len(ix) * 8e-4 * np.mean(w) / H / T) * N.ANN, status='COMPUTED'))
                        rows_mir.append(dict(segment=seg_name, form=form, object_key=key, trigger=tg, H=H, horizon_mode=hm, mirror=mir, n_events=int(len(ix)),
                                             gross_bp_per_event_mean=float(np.mean(evs)), gross_bp_per_event_se=float(np.std(evs, ddof=1) / np.sqrt(len(evs))) if len(evs) > 1 else np.nan,
                                             stock_excess_bp_mean=float(np.mean(exC)), status='COMPUTED'))
                    ev_store['%s|%s|%s|H%d|%s' % (form, key, tg, H, hm)] = np.vstack([f, c, w, e_early, end, evC, evN, exC])
                    # 对照（CVR_JUMP，FIXED_H，CASH 条件改善 = 每事件 bp）
                    if tg == 'CVR_JUMP' and hm == 'FIXED_H':
                        real_cond = float(np.mean(evC))
                        for ctl, vals, st_c in controls(tb, cb, wb, td, st_, P, H, T, r0, bench, run, seg_name, form, key):
                            rows_ctl.append(dict(segment=seg_name, form=form, object_key=key, trigger=tg, H=H, control=ctl, real_cond_bp_per_event=real_cond,
                                                 control_cond_bp_per_event_mean=float(np.nanmean(vals)) if len(vals) else np.nan,
                                                 control_cond_bp_per_event_sd=float(np.nanstd(vals, ddof=1)) if len(vals) > 1 else np.nan, paths=len(vals),
                                                 real_minus_control_bp=real_cond - float(np.nanmean(vals)) if len(vals) else np.nan, n_events_real=int(len(ix)),
                                                 status=st_c))
        N.log('B2 %s %s %s 完成（%.0f s）' % (seg_name, form, key, time.time() - t0))
    od = N.P('results', phase, 'b2')
    os.makedirs(od, exist_ok=True)
    outs = []
    for nm, rows in (('b2_risk_set_%s__%s.csv' % (seg_name, tagf), rows_rs), ('b2_order_overlay_%s__%s.csv' % (seg_name, tagf), rows_ov), ('b2_mirrors_%s__%s.csv' % (seg_name, tagf), rows_mir),
                     ('b2_controls_%s__%s.csv' % (seg_name, tagf), rows_ctl)):
        p = os.path.join(od, nm)
        N.atomic_write_csv(p, N.to_status(pd.DataFrame(rows)))
        outs.append(p)
    pe = os.path.join(od, 'b2_events_%s__%s.npz' % (seg_name, tagf))
    N.atomic_write_npz(pe, keys=np.array(list(ev_store.keys()), dtype='U'), **{('e%04d' % i): v for i, v in enumerate(ev_store.values())},
                       rows=np.array(['f', 'c', 'w', 'e_early', 'end', 'cash_bp', 'next_bp', 'stock_excess_bp'], dtype='U'))
    outs.append(pe)
    return outs, time.time() - t0


def controls(tb, cb, wb, td, st_, P, H, T, r0, bench, run, seg_name, form, key):
    """同率随机（64 路径）/ CVR 水平最差 / 伯努利风险镜像：同日 × 同持有日龄层；返回 [(名, 每路径条件改善 bp 数组, 状态)]。
    风险集（日 d）= e0 ≤ d ≤ n−2 且本镜像未移出的批次；日龄 = d − e0。伯努利率 = 过去 60 日同日龄真实首次触发数 / 风险批次日数（≥ 20 有效日，否则该层不抽）。"""
    import e6j_random as RND
    real_trig = (st_ != B2.NOT_TRIGGERED) & (st_ != B2.NOT_ENTERED)
    e0 = tb + 1
    nn = tb + H + 1
    nb = len(tb)
    last = np.minimum(nn - 2, T - 1)
    span = np.maximum(last - e0 + 1, 0)
    bid = np.repeat(np.arange(nb), span)
    day = np.concatenate([np.arange(e0[i], last[i] + 1) for i in range(nb) if span[i] > 0]) if span.sum() else np.zeros(0, np.int64)
    o = np.argsort(day, kind='stable')
    bid, day = bid[o], day[o]
    ptr = np.searchsorted(day, np.arange(T + 1))
    age_all = day - e0[bid]
    Cn = np.zeros((T, H + 1))
    for d_, ag in zip(td[real_trig], td[real_trig] - e0[real_trig]):
        if 0 <= ag <= H and 0 <= d_ < T:
            Cn[int(d_), int(ag)] += 1
    Rk = np.zeros((T, H + 1))
    if len(day):
        np.add.at(Rk, (day, np.clip(age_all, 0, H)), 1)
    c60 = np.cumsum(np.vstack([np.zeros((1, H + 1)), Cn]), 0)
    r60 = np.cumsum(np.vstack([np.zeros((1, H + 1)), Rk]), 0)
    v60 = np.cumsum(np.vstack([np.zeros((1, H + 1)), (Rk > 0).astype(float)]), 0)

    def outcome(i, d):
        a = max(e0[i] + 1, d + 1)
        if a >= nn[i]:
            return np.nan
        e = -1
        for x in range(a, T):
            if P['sell'][x, cb[i]]:
                e = x
                break
        b = min(nn[i], T - 1)
        if e < 0 or e >= b:
            return np.nan
        tt = np.arange(e + 1, b + 1)
        den = np.minimum(tt - 1, H).astype(float)
        return float((-(wb[i] / den) * (r0[tt, cb[i]] - bench[tt])).sum() * 1e4)
    out = []
    tdays = sorted(set(int(x) for x in np.flatnonzero(Cn.sum(1) > 0)))
    for ctl in ('SAME_RATE_RANDOM', 'CVR_LEVEL_WORST', 'BERNOULLI_RISK'):
        paths = range(NPATH) if ctl != 'CVR_LEVEL_WORST' else range(1)
        vals, short, unk = [], 0, 0
        for p in paths:
            exited = np.zeros(nb, bool)
            ev = []
            for d in (tdays if ctl != 'BERNOULLI_RISK' else range(T)):
                li = bid[ptr[d]:ptr[d + 1]]
                li = li[~exited[li]]
                if not len(li):
                    continue
                ages = d - e0[li]
                sel = []
                for ag in np.unique(ages):
                    cand = li[ages == ag]
                    if ctl == 'BERNOULLI_RISK':
                        lo = max(0, d - 60)
                        if v60[d, ag] - v60[lo, ag] < 20:
                            unk += 1
                            continue
                        rate = (c60[d, ag] - c60[lo, ag]) / max(1.0, r60[d, ag] - r60[lo, ag])
                        u = RND.uniform(RND.path_key('E6n.B2.BERNOULLI', '%s|%s' % (form, key), seg_name, 'H%d' % H, 'IID', p), np.full(len(cand), d), cand)
                        sel += list(cand[u < rate])
                        continue
                    m = int(Cn[d, ag])
                    if not m:
                        continue
                    if len(cand) < m:
                        short += 1
                        m = len(cand)
                    if ctl == 'SAME_RATE_RANDOM':
                        u = RND.uniform(RND.path_key('E6n.B2.SAME_RATE', '%s|%s' % (form, key), seg_name, 'H%d' % H, 'IID', p), np.full(len(cand), d), cand)
                        sel += list(cand[np.argsort(-u, kind='stable')[:m]])
                    else:
                        lv = P['cvr_pct'][d, cb[cand]]
                        lv = np.where(np.isfinite(lv), lv, -1.0)
                        sel += list(cand[np.lexsort((cb[cand], -lv))[:m]])
                for i in sel:
                    exited[i] = True
                    v = outcome(i, d)
                    if np.isfinite(v):
                        ev.append(v)
            vals.append(float(np.mean(ev)) if ev else np.nan)
        st = 'COMPUTED'
        if short:
            st = 'BUDGET_SHORTFALL（%d 日层）' % short
        if ctl == 'BERNOULLI_RISK' and unk and all(not np.isfinite(v) for v in vals):
            st = 'UNKNOWN'
        out.append((ctl, np.asarray(vals, float), st))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--forms', default='')
    a = ap.parse_args()
    import e6n_gate as GT
    GT.deriv_ready(a.seg, 'B2 run %s' % a.seg)
    phase = 'deriv' if a.seg in N.DERIV_SEGS else 'full'
    outs, wall = run_seg(a.seg, phase, [f for f in a.forms.split(',') if f] or None)
    N.write_receipt('E6n_b2_run_%s_%s' % (a.seg, a.forms.replace(',', '_') or 'ALL'), outs, code=[__file__, B2.__file__], wall_s=round(wall, 1))
    print(json.dumps(dict(seg=a.seg, wall_s=round(wall, 1)), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
