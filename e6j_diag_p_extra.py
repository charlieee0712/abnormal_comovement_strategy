# -*- coding: utf-8 -*-
"""E6j P 块诊断补充（plan §5.1a / §8.5）：主配置 α .25；六形态 × 四个非恒等臂；一段一个进程。
  CS_FROZEN   COMMON_SUPPORT 附表：J 上只缩域、保留全池已估评分（q0 与新分量的全池中性化 / 排序不在 J 上重估），
              C0F / C1F 与闭合 N1−N0 = (C1F−C0F)+(C0F−N0)+(N1−C1F)；H{3,5,10,20}。不与重估 CS（e6j_diag_p）混称。
  SHADOW_SF   自融资 shadow（capital = 日初 NAV，ideal / X1）母与子的 NAV 路径（H5）：逐段账户财富最大回撤；
              源 net8 的"超额路径回撤"另在 e6j_policy_extra 从封存账户算，两者定义分开、不互换。各段独立起点（段间不连续，不拼接）。
  EDIT_CAP    形成日编辑资本占比（H5 目标权重）：子在换入者上的权重份额、母在换出者上的权重份额、有编辑日比例。
写 diagnostics/P/<段>/diag_extra_<段>.csv 与 shadow_nav_<段>.npz。纳入 P 包封存（e6j_seal）后再读。"""
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
import e6j_diag_p as DP

OUT = os.path.join(J.RES, 'diagnostics', 'P')
HS = EN.HS_P
A = DP.A


def max_dd(nav):
    x = np.asarray(nav, float); f = np.isfinite(x) & (x > 0)
    if f.sum() < 2:
        return np.nan
    y = x[f]; peak = np.maximum.accumulate(y)
    return float(np.max(1.0 - y / peak))


def run(pname):
    t0 = time.time()
    ok, why = RP.registration_ok()
    if not ok:
        raise RuntimeError('登记门：%s' % why)
    env = EN.Env(pname, with_prod=True)
    ctx, ci, S, T = env.ctx, env.ci, env.S, env.S.T
    od = os.path.join(OUT, pname); os.makedirs(od, exist_ok=True)
    comps = {k: env._dense_cells(SL.member_pct(ctx, mid, d)[0]) for k, (mid, d) in DP.COMP.items()}
    import e6g_c as GC
    SC = GC.ShadowCtx(S)
    rows, navs = [], {}
    for form in P.DELIV:
        st = EN.prod_structure(env, form)
        parent = st.kept(st.q0[None, :])[0]
        ledP, (tb, cb, wb) = DP.ledgers(env, parent)
        # ---- 母 shadow（自融资）
        idx, val = DP.split_days(tb, cb, wb, T)
        Wp = GC.target_weights(S, idx, val, 5)
        for mode in ('ideal', 'X1'):
            sh = GC.shadow_account(SC, Wp, mode=mode, capital='self_financing')
            navs['%s|parent|%s' % (form, mode)] = sh['nav']
            rows.append(dict(segment=pname, form=form, arm='C0', H=5, diag='SHADOW_SF_%s' % mode, max_dd=max_dd(sh['nav']),
                             nav_end_over_start=float(sh['nav'][np.isfinite(sh['nav'])][-1] / (5 * GC.YI)) if np.isfinite(sh['nav']).any() else np.nan,
                             recon_max_abs=float(np.nanmax(np.abs(sh['recon'])))))
        for arm, parts in DP.ARMS.items():
            qch = EN.blend(st.q0, [(sh_, comps[m][None, :]) for sh_, m in parts], A)
            child = st.kept(qch)[0]
            ledC, (tc, cc, wc) = DP.ledgers(env, child)
            # ---- CS_FROZEN：J 外置缺，J 内保留全池评分
            J_ = np.isfinite(st.q0)
            for _, m in parts:
                J_ &= np.isfinite(comps[m])
            q0F = np.where(J_, st.q0, np.nan)
            stF = EN.prod_structure(env, form, q0=q0F)
            c0 = stF.kept(stF.q0[None, :])[0]
            c1 = stF.kept(EN.blend(stF.q0, [(sh_, np.where(J_, comps[m], np.nan)[None, :]) for sh_, m in parts], A))[0]
            ledC0, _ = DP.ledgers(env, c0); ledC1, _ = DP.ledgers(env, c1)
            for H in HS:
                n0, n1, x0, x1 = ledP[H][3], ledC[H][3], ledC0[H][3], ledC1[H][3]
                rows.append(dict(segment=pname, form=form, arm=arm, H=H, diag='CS_FROZEN',
                                 N1_minus_N0=DP.ann(n1 - n0), C1F_minus_C0F=DP.ann(x1 - x0), C0F_minus_N0=DP.ann(x0 - n0), N1_minus_C1F=DP.ann(n1 - x1),
                                 closure_resid=DP.ann((n1 - n0) - ((x1 - x0) + (x0 - n0) + (n1 - x1))), J_share=float(J_.mean()),
                                 cells_C0F_vs_N0=int((c0 != parent).sum()), cells_C1F_vs_N1=int((c1 != child).sum())))
            # ---- 子 shadow（自融资）
            idx, val = DP.split_days(tc, cc, wc, T)
            Wc = GC.target_weights(S, idx, val, 5)
            for mode in ('ideal', 'X1'):
                sh = GC.shadow_account(SC, Wc, mode=mode, capital='self_financing')
                navs['%s|%s|%s' % (form, arm, mode)] = sh['nav']
                rows.append(dict(segment=pname, form=form, arm=arm, H=5, diag='SHADOW_SF_%s' % mode, max_dd=max_dd(sh['nav']),
                                 nav_end_over_start=float(sh['nav'][np.isfinite(sh['nav'])][-1] / (5 * GC.YI)) if np.isfinite(sh['nav']).any() else np.nan,
                                 recon_max_abs=float(np.nanmax(np.abs(sh['recon'])))))
            # ---- EDIT_CAP（形成日目标权重）
            Wb_ = np.zeros((T, ci.Nc)); Wb_[tb, cb] = wb
            Wc_ = np.zeros((T, ci.Nc)); Wc_[tc, cc] = wc
            P_ = Wb_ > 0; C_ = Wc_ > 0
            ent = (C_ & ~P_); ext = (P_ & ~C_)
            sc_, sp_ = Wc_.sum(1), Wb_.sum(1)
            f = (sc_ > 0) & (sp_ > 0)
            rows.append(dict(segment=pname, form=form, arm=arm, H=5, diag='EDIT_CAP',
                             entry_weight_share_mean=float(np.mean((Wc_ * ent).sum(1)[f] / sc_[f])) if f.any() else np.nan,
                             exit_weight_share_mean=float(np.mean((Wb_ * ext).sum(1)[f] / sp_[f])) if f.any() else np.nan,
                             edit_day_share=float(np.mean((ent | ext).any(1)[f])) if f.any() else np.nan, days=int(f.sum())))
            J.log('  %s %s %s diag_extra done %.0fs' % (pname, form, arm, time.time() - t0), os.path.join(J.RES, 'logs', 'diag_p_extra_%s.log' % pname))
    df = pd.DataFrame(rows)
    p = os.path.join(od, 'diag_extra_%s.csv' % pname); J.atomic_write_csv(p, df)
    pn = os.path.join(od, 'shadow_nav_%s.npz' % pname)
    keys = sorted(navs)
    J.atomic_write_npz(pn, keys=np.array(keys), nav=np.vstack([navs[k] for k in keys]), dates=np.array([str(d)[:10] for d in env.dates]))
    J.write_receipt('diag_p_extra_%s' % pname, [p, pn], 'SUCCEEDED', n=len(df), wall_s=round(time.time() - t0, 1))
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1]))
