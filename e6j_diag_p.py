# -*- coding: utf-8 -*-
"""E6j P 块诊断（plan §4.1a / §5.1a / §6.1–§6.3 / §7.6）：主对象 = 4 个非恒等臂 × 6 形态 × α .25；一段一个进程。
  CS      COMMON_SUPPORT 四账户（N0 原生母 / N1 原生子 / C0 共同支持母 / C1 共同支持子），J = 全部必要新分量有效 ∩ q0 定义域；
          在 J 上按源规则重做 K 与新分量的市值中性化和排名（其余母体输入不变）；H{3,5,10,20}；闭合 N1−N0 = (C1−C0)+(C0−N0)+(N1−C1)
  TR      TRANSPORT（J 内按新残差坏度把 J 内 q0 有序值逐一分配，平局取均值，J 外保留 q0）；H{3,5,10,20}
  TREFIT  A4b 两形态：V00 / V10 / V01 / V11（第一关新 / 旧 × 第二关 T 模型拟合于新 / 旧第一关集合），顺序平均分解；H5
  MATCHN  同最终人数的原核排序账户（plan §6.3 全序；先剔既有 CVR 毒尾）；源 N 端点须复现源名单；H{3,5,10,20}
  EDIT    决策编辑账本：形成日 换入 / 换出 / 共同再定权 分原因（A4b 细分 K 第一关 / T 第二关）；线性批次映射滚到收益日的 gross 贡献；H5
  SHADOW  同一账户模型下全可成交（ideal）与有限制库存账户（X1：买卖标志）vs 源引擎；H5
写 diagnostics/P/<段>/*.csv 与 npz。"""
import e6j_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_engine as EN
import e6j_run_p as RP
import comprehensive_factor_diagnosis as C

OUT = os.path.join(J.RES, 'diagnostics', 'P')
HS = EN.HS_P
ARMS = {'S': [(1.0, 'S')], 'M': [(1.0, 'M')], 'SM': [(0.5, 'S'), (0.5, 'M')], 'C1': [(1.0, 'C1')]}
COMP = {'S': ('K_rar20', 'lo'), 'M': ('K_slope20', 'lo'), 'C1': ('K_MA3_E6F', 'hi')}
A = 0.25


def ledgers(env, kept, Hs=HS):
    ci, SE = env.ci, env.SE
    t, c = ci.t[kept], ci.c[kept]; w = SE.dev(t, c)
    return SE.pnl(t, c, w, Hs, 8.0), (t, c, w)


def ann(x):
    return float(np.nanmean(x)) * J.ANN


def cells_bool_to_pool(env, b):
    ci, S = env.ci, env.S
    m = np.zeros(S.pool0.shape, bool)
    m[ci.t[b], np.asarray(S.ccols)[ci.c[b]]] = True
    return pd.DataFrame(m.astype(float), index=S.pool0.index, columns=S.pool0.columns)


def cs_pct(env, raw_full, pool_J, direction):
    """在 J（pool0 ∧ J）上重做 log 市值 OLS 与排名 → 单元（J 外 NaN）。"""
    cache = C.precompute_neutralized_factor(raw_full, pool_J, env.ctx['log_mcap'])
    return env._dense_cells(SL.pct_dir(cache, direction))


def stage2_with_model(env, s1_cells, fit_cells, M, pctkeep=50):
    """T 第二关：模型（逐日 OLS 系数）拟合于 fit_cells，评价于 s1_cells（源 neutralize_by_mcap 口径：拟合集有效 < 10 → 原值）；
       评价集内平均秩 pct → 源 keep（有效 < 3g 当日空；qcut 前缀；并列按列位）。返回 kept 单元。"""
    import e6i_randoms as IR
    ci = env.ci
    T = ci.T
    x = env.R.logm_c; y = M.T_raw_c
    out = np.zeros(ci.n, bool)
    for t in range(T):
        sl = np.flatnonzero(ci.t == t)
        if not len(sl):
            continue
        fit = sl[fit_cells[sl]]; ev = sl[s1_cells[sl]]
        if len(ev) < 6:
            continue
        fv = fit[np.isfinite(x[fit]) & np.isfinite(y[fit])]
        if len(fv) >= 10:
            xm, ym = x[fv].mean(), y[fv].mean()
            b = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv]); a = ym - b * xm
            val = y[ev] - (a + b * x[ev])
        else:
            val = y[ev].copy()
        ok = np.isfinite(val)
        if ok.sum() < 6:
            continue
        evv, vv = ev[ok], val[ok]
        pct = pd.Series(vv).rank(pct=True).to_numpy()
        n = len(evv)
        K = IR.k_of(n, pctkeep)
        order = np.lexsort((ci.c[evv], pct))
        out[evv[order[:K]]] = True
    return out


def run(pname):
    t0 = time.time()
    ok, why = RP.registration_ok()
    if not ok:
        raise RuntimeError('登记门：%s' % why)
    env = EN.Env(pname, with_prod=True)
    ctx, ci, SE, S, T = env.ctx, env.ci, env.SE, env.S, env.S.T
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    comps, raws, neus = {}, {}, {}
    for k, (mid, d) in COMP.items():
        pc, neu, _ = SL.member_pct(ctx, mid, d)
        comps[k] = env._dense_cells(pc); neus[k] = neu
        raws[k] = SL.full_frame(ctx, SL.e6i_member_raw(pname, mid)[0])
    k0raw = ctx['specs'][P.F_COND]['func'](ctx['data'], ctx['feats'], ctx['industry'])
    rows = []
    # ---------------- CS / TR / MATCHN / EDIT / SHADOW 逐形态
    import e6g_c as GC
    SC = GC.ShadowCtx(S)
    for form in P.DELIV:
        st = EN.prod_structure(env, form)
        parent = st.kept(st.q0[None, :])[0]
        ledP, (tb, cb, wb) = ledgers(env, parent)
        for arm, parts in ARMS.items():
            child = st.kept(EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in parts], A))[0]
            ledC, (tc, cc, wc) = ledgers(env, child)
            # ---- COMMON_SUPPORT
            J_ = np.isfinite(st.q0)
            for _, m in parts:
                J_ &= np.isfinite(comps[m])
            poolJ = cells_bool_to_pool(env, J_)
            q0J = cs_pct(env, k0raw, poolJ, 'hi')
            newJ = {m: cs_pct(env, raws[m], poolJ, COMP[m][1]) for _, m in parts}
            stJ = EN.prod_structure(env, form, q0=q0J)
            c0 = stJ.kept(stJ.q0[None, :])[0]
            c1 = stJ.kept(EN.blend(stJ.q0, [(sh, newJ[m][None, :]) for sh, m in parts], A))[0]
            ledC0, _ = ledgers(env, c0); ledC1, _ = ledgers(env, c1)
            # ---- TRANSPORT
            trn = {m: env._dense_cells(SL.transport(ctx['pcond'], neus[m], COMP[m][1])) for _, m in parts}
            ktr = st.kept(EN.blend(st.q0, [(sh, trn[m][None, :]) for sh, m in parts], A))[0]
            ledTR, _ = ledgers(env, ktr)
            for H in HS:
                n0, n1, x0, x1, tr = ledP[H][3], ledC[H][3], ledC0[H][3], ledC1[H][3], ledTR[H][3]
                rows.append(dict(segment=pname, form=form, arm=arm, H=H, diag='CS',
                                 N1_minus_N0=ann(n1 - n0), C1_minus_C0=ann(x1 - x0), C0_minus_N0=ann(x0 - n0), N1_minus_C1=ann(n1 - x1),
                                 closure_resid=ann((n1 - n0) - ((x1 - x0) + (x0 - n0) + (n1 - x1))), J_share=float(J_.mean()),
                                 cells_C0_vs_N0=int((c0 != parent).sum()), cells_C1_vs_N1=int((c1 != child).sum())))
                rows.append(dict(segment=pname, form=form, arm=arm, H=H, diag='TRANSPORT', SRC_minus_parent=ann(n1 - n0),
                                 TR_minus_parent=ann(tr - n0), SRC_minus_TR=ann(n1 - tr), cells_TR_vs_SRC=int((ktr != child).sum())))
            # ---- MATCHN（同最终人数的原核排序账户）；源 N 端点须复现源名单
            mn = matched_n(env, form, st, parent, child)
            endpoint = matched_n(env, form, st, parent, parent)
            ledM, _ = ledgers(env, mn)
            for H in HS:
                rows.append(dict(segment=pname, form=form, arm=arm, H=H, diag='MATCHN', child_minus_matchN=ann(ledC[H][3] - ledM[H][3]),
                                 matchN_minus_parent=ann(ledM[H][3] - ledP[H][3]), n_equal_days=int((np.bincount(ci.t[mn], minlength=T) ==
                                                                                                   np.bincount(ci.t[child], minlength=T)).sum()),
                                 endpoint_cells_differ=int((endpoint != parent).sum())))
            # ---- EDIT（H5）
            qch = EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in parts], A)
            rows.extend(edit_ledger(env, form, st, parent, child, (tb, cb, wb), (tc, cc, wc), pname, arm, qch,
                                    ann(ledC[5][0] - ledP[5][0])))
            # ---- SHADOW（H5）
            for lab, (t_, c_, w_) in (('parent', (tb, cb, wb)), ('child', (tc, cc, wc))):
                idx, val = split_days(t_, c_, w_, T)
                W = GC.target_weights(S, idx, val, 5)
                for mode in ('ideal', 'X1'):
                    sh = GC.shadow_account(SC, W, mode=mode)
                    rows.append(dict(segment=pname, form=form, arm=arm, H=5, diag='SHADOW_%s_%s' % (mode, lab), excess_ann=ann(sh['excess']),
                                     unfilled_buy=float(np.nansum(sh['unfilled_buy'])), unfilled_sell=float(np.nansum(sh['unfilled_sell'])),
                                     trapped_mean=float(np.nanmean(sh['trapped']))))
            J.log('  %s %s %s diag done %.0fs' % (pname, form, arm, time.time() - t0), os.path.join(J.RES, 'logs', 'diag_p_%s.log' % pname))
        if form.startswith('A4b'):
            rows.extend(trefit(env, form, st, parent, comps, pname))
    df = pd.DataFrame(rows)
    p = os.path.join(od, 'diagnostics_%s.csv' % pname); J.atomic_write_csv(p, df)
    J.write_receipt('diag_p_%s' % pname, [p], 'SUCCEEDED', n=len(df), wall_s=round(time.time() - t0, 1))
    return 0


def split_days(t, c, w, T):
    order = np.argsort(t, kind='stable'); ts = t[order]; bnd = np.searchsorted(ts, np.arange(T + 1))
    return [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)], [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]


def matched_n(env, form, st, parent, child):
    """plan §6.3：先剔既有 CVR 毒尾；在合法剩余域按父的全序取与真实子同日同数的前 N。
       Mmean：原均值坏度；A4b：三级（源最终核心保留 → 源第一关保留 → 其余技术合法），级内按原 T 模型 pool0 预测坏度、原 K 坏度、列位；
       Munion：三腿全过 → 缺一 → 缺二 → 其余，级内按三腿 worst-rank、列位。"""
    ci = env.ci
    T = ci.T
    legal = ~env.cvr if form.endswith('_CVRv5') else np.ones(ci.n, bool)
    if form.startswith('M_mean3'):
        key1 = np.zeros(ci.n); key2 = st.score(st.q0[None, :])[0]; key3 = np.zeros(ci.n)
    elif form.startswith('A4b'):
        M = st.M
        s1 = st.dom.keep(st.q0[None, st.dom.ids])[0]
        s1c = np.zeros(ci.n, bool); s1c[st.dom.ids[s1]] = True
        import e6i_randoms as IR
        core = IR.dep_stage2_keep(env.R, M, s1c[None, :], st.b)[0]
        key1 = np.where(core, 0, np.where(s1c, 1, 2)).astype(float)
        x = env.R.logm_c; y = M.T_raw_c
        tpred = np.full(ci.n, np.nan)
        for t in range(T):
            sl = np.flatnonzero(ci.t == t)
            fit = sl[s1c[sl]]
            fv = fit[np.isfinite(x[fit]) & np.isfinite(y[fit])]
            if len(fv) >= 10:
                xm, ym = x[fv].mean(), y[fv].mean(); b = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv])
                tpred[sl] = y[sl] - (ym - b * xm + b * x[sl])
            else:
                tpred[sl] = y[sl]
        key2 = tpred; key3 = st.q0
    else:
        dK = ~(st.dom.keep(st.q0[None, st.dom.ids])[0])
        kk = np.zeros(ci.n, bool); kk[st.dom.ids[~dK]] = True
        fails = (~kk).astype(int) + env.dT.astype(int) + env.dR.astype(int)
        key1 = np.minimum(fails, 3).astype(float)
        key2 = np.fmax(np.fmax(np.nan_to_num(env.pK, nan=9), np.nan_to_num(env.pT, nan=9)), np.nan_to_num(env.pR, nan=9))
        key3 = np.zeros(ci.n)
    out = np.zeros(ci.n, bool)
    nc = np.bincount(ci.t[child], minlength=T)
    for t in range(T):
        sl = np.flatnonzero((ci.t == t) & legal)
        if nc[t] == 0 or not len(sl):
            continue
        k2 = np.where(np.isfinite(key2[sl]), key2[sl], np.inf); k3 = np.where(np.isfinite(key3[sl]), key3[sl], np.inf)
        o = np.lexsort((ci.c[sl], k3, k2, key1[sl]))
        out[sl[o[:nc[t]]]] = True
    return out


def edit_ledger(env, form, st, parent, child, pw, cw, pname, arm, qch, dgross_total):
    """形成日 ΔW 分原因（互斥，冻结优先级：K 第一关编辑 → T 第二关编辑 → 共同再定权；FALLBACK 下支持域不变、否决两边相同），
       线性批次映射到收益日（H5），各原因 gross 贡献之和 = 子 − 母 gross（闭合行另列；费用单列）。"""
    ci, S = env.ci, env.S
    T, Nc = ci.T, ci.Nc
    (tb, cb, wb), (tc, cc, wc) = pw, cw
    Wb = np.zeros((T, Nc)); Wb[tb, cb] = wb
    Wc = np.zeros((T, Nc)); Wc[tc, cc] = wc
    dW = Wc - Wb
    P_ = np.zeros((T, Nc), bool); P_[ci.t[parent], ci.c[parent]] = True
    C_ = np.zeros((T, Nc), bool); C_[ci.t[child], ci.c[child]] = True
    reason = np.full((T, Nc), 3, np.int8)                # 3 = 共同再定权
    edit = P_ ^ C_
    if form.startswith('A4b'):
        def s1_of(q):
            b = np.zeros(ci.n, bool); b[st.dom.ids[st.dom.keep(q[:, st.dom.ids])[0]]] = True
            D = np.zeros((T, Nc), bool); D[ci.t[b], ci.c[b]] = True
            return D
        S1o, S1n = s1_of(st.q0[None, :]), s1_of(qch)
        gate = (C_ & ~P_ & ~S1o) | (P_ & ~C_ & ~S1n)    # 换入者原不在旧第一关 / 换出者不在新第一关
        reason[edit & gate] = 0
        reason[edit & ~gate] = 1                         # 两关成员都在、第二关（T 重估）改变
    else:
        reason[edit] = 0
    H = 5
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    out = []
    r0, bench = S.r0, S.bench
    tot = 0.0
    for g, lab in ((0, 'K_gate_edit'), (1, 'T_stage2_edit'), (3, 'common_reweight')):
        dWg = np.where(reason == g, dW, 0.0)
        cs = np.cumsum(dWg, axis=0)
        act = cs.copy(); act[H:] -= cs[:-H]
        act = act / den[:, None]
        port = np.zeros(T); pos = np.zeros(T)
        port[2:] = np.einsum('tc,tc->t', r0[2:], act[:-2]); pos[2:] = act[:-2].sum(1)
        gross = port - bench * pos
        tot += ann(gross)
        out.append(dict(segment=pname, form=form, arm=arm, H=H, diag='EDIT_%s' % lab, gross_contrib_ann=ann(gross),
                        edit_cells=int(((reason == g) & edit).sum() if g != 3 else ((P_ & C_) & (np.abs(dW) > 0)).sum())))
    out.append(dict(segment=pname, form=form, arm=arm, H=H, diag='EDIT_closure', gross_contrib_ann=tot, total_dgross_ann=dgross_total,
                    closure_resid=tot - dgross_total))
    return out


def trefit(env, form, st, parent, comps, pname):
    """A4b：V00 母、V11 原生子、V10 新第一关 + 旧 T 模型、V01 旧第一关 + 新 T 模型；顺序平均 A / B 贡献（算法作用分解，非经济中介）。"""
    ci = env.ci
    M = st.M
    s1_old = np.zeros(ci.n, bool); s1_old[st.dom.ids[st.dom.keep(st.q0[None, st.dom.ids])[0]]] = True
    out = []
    for arm, parts in ARMS.items():
        q = EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in parts], A)
        s1_new = np.zeros(ci.n, bool); s1_new[st.dom.ids[st.dom.keep(q[:, st.dom.ids])[0]]] = True
        V = {}
        for lab, ev, fit in (('V00', s1_old, s1_old), ('V11', s1_new, s1_new), ('V10', s1_new, s1_old), ('V01', s1_old, s1_new)):
            k = stage2_with_model(env, ev, fit, M, st.b) & ~st.drop
            V[lab] = ledgers(env, k, (5,))[0][5][3]
        A_ = 0.5 * ((V['V10'] - V['V00']) + (V['V11'] - V['V01'])); B_ = 0.5 * ((V['V01'] - V['V00']) + (V['V11'] - V['V10']))
        out.append(dict(segment=pname, form=form, arm=arm, H=5, diag='TREFIT', V11_minus_V00=ann(V['V11'] - V['V00']),
                        A_first_gate=ann(A_), B_T_refit=ann(B_), resid=ann((V['V11'] - V['V00']) - A_ - B_),
                        V00_vs_parent_cells=int(((stage2_with_model(env, s1_old, s1_old, M, st.b) & ~st.drop) != parent).sum())))
    return out


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
