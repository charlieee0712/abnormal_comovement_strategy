# -*- coding: utf-8 -*-
"""E6k 对照分布（附录 C；诊断，不作门，plan §9.3 明令不据此改门）。一段一个进程，封存之后运行。
对象：24 个 NATIVE 主配置（四测量 × 六形态，α .25 × H5）。
  C0     恒等（子 = 父）：全部差恒为 0（机械核对）
  C1     NATIVE_C1 主配置（六形态）：逐日量的分布
  LEGACY LEGACY_POLICY_RANDOM 前 256 条路径（与随机层同键、同机制，确定性重算目标）
  IID    NEW_COND_ISK_IID 前 256 条路径
逐路径（或逐日）量：组合层 size 差中点（T / LAG1，×100）、编辑层 gap（T，×100，带符号）、小盘 30% 份额差、Δturn（相对父）、冲击 net 差（A 5 亿 κ .5，H5）。
输出 diagnostics/control_distributions/<段>.csv（q10 / q50 / q90 / p95 与均值；标注"未用于任何门值"）。"""
import e6k_boot  # noqa: F401
import os
import sys
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_seal as SEAL
import e6j_stats as ST

NP = 256


def summarize(kind, did, name, x):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if not len(x):
        return None
    return dict(kind=kind, desc_id=did, metric=name, n=len(x), mean=float(x.mean()), q10=float(np.percentile(x, 10)), q50=float(np.percentile(x, 50)),
                q90=float(np.percentile(x, 90)), p95=float(np.percentile(np.abs(x), 95)), p95_signed_upper=float(np.percentile(x, 95)),
                note='诊断分布；未用于任何门值')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    a = ap.parse_args()
    pname = a.segment
    ok, bad = SEAL.verify('deriv' if pname in K.DERIV_SEGS else 'post')
    if not ok:
        raise RuntimeError('封存核对失败：%s' % bad[:5])
    import e6k_env as E
    import e6k_acct as AC
    import e6k_random as RN
    import e6k_run_det as RD
    import e6j_fast as FAST
    seg = E.Seg(pname)
    acct = AC.Acct(seg)
    rows = []
    for p in E.P6:
        st = seg.struct(p)
        st.stage2 = FAST.stage2_fast
        k0 = st.q0
        base = RD.Ctx(seg, st, k0, seg.kf('C1'))
        tp = acct.target(base.parent)
        lp = acct.ledgers(tp, (5,), roll=False)[5]
        # C0
        rows.append(dict(kind='C0', desc_id='K0|%s|a0|H5|PARENT' % p, metric='all', n=1, mean=0.0, q10=0.0, q50=0.0, q90=0.0, p95=0.0,
                         p95_signed_upper=0.0, note='恒等：子 = 父，全部差恒为 0'))
        for f in ('S', 'M', 'Q', 'C1'):
            kf = seg.kf(f)
            ctx = RD.Ctx(seg, st, k0, kf)
            did = '%s|%s|a0.25|H5|NATIVE' % (f, p)
            if f == 'C1':
                kept = ctx.child(0.25)
                tg = acct.target(kept)
                s = acct.target_stats(tg, kept, ctx.parent, tp)
                for nm, x in (('port_size_mid_T', 0.5 * (s['szT_lo'] + s['szT_hi'])), ('port_size_mid_LAG1', 0.5 * (s['szL_lo'] + s['szL_hi'])),
                              ('edit_gap_T', s['gapT'] * 100.0), ('small30_delta', s['small30'] - acct.target_stats(tp, ctx.parent)['small30'])):
                    r = summarize('C1_daily', did, nm, x)
                    if r:
                        rows.append(r)
            for mech in ('LEGACY_POLICY_RANDOM', 'NEW_COND_ISK_IID'):
                if mech == 'LEGACY_POLICY_RANDOM':
                    kf_hi = None
                    if RN.legacy_kind(p, f) == 'B':
                        import e6j_slot as SL
                        neu = SL.neu_of(seg.ctx, SL.full_frame(seg.ctx, seg.raw(f)))
                        kf_hi = kf if E.MEAS[f][2] == 'hi' else seg.env._dense_cells(SL.pct_dir(neu, 'hi'))
                    perm = RN.Legacy(seg, p, f, kf, kf_hi)
                else:
                    perm = RN.NewCond(seg, f, kf, k0, 'ISK', 1)
                vals = {k: [] for k in ('port_size_mid_T', 'port_size_mid_LAG1', 'edit_gap_T', 'small30_delta', 'dturn_rel', 'impact_net_diff')}
                for path in range(NP):
                    kp = perm.draw(path)
                    q = np.where(np.isfinite(kp), 0.75 * k0 + 0.25 * kp, k0)
                    kept = st.kept(q[None, :])[0]
                    tg = acct.target(kept)
                    s = acct.target_stats(tg, kept, ctx.parent, tp)
                    led = acct.ledgers(tg, (5,), roll=False)[5]
                    vals['port_size_mid_T'].append(np.nanmean(0.5 * (s['szT_lo'] + s['szT_hi'])))
                    vals['port_size_mid_LAG1'].append(np.nanmean(0.5 * (s['szL_lo'] + s['szL_hi'])))
                    vals['edit_gap_T'].append(np.nanmean(s['gapT']) * 100.0 if np.isfinite(s['gapT']).any() else np.nan)
                    vals['small30_delta'].append(np.nanmean(s['small30']) - np.nanmean(acct.target_stats(tp, ctx.parent)['small30']))
                    vals['dturn_rel'].append(np.mean(led['turn']) / np.mean(lp['turn']) - 1.0 if np.mean(lp['turn']) > 0 else np.nan)
                    ci_ = led['net8'] - ST.impact_cost(led['bracket'], 5.0, 0.5)
                    pi_ = lp['net8'] - ST.impact_cost(lp['bracket'], 5.0, 0.5)
                    vals['impact_net_diff'].append(ST.seg_D(ST.paired(ci_, pi_)[0])[0])
                for nm, x in vals.items():
                    r = summarize(mech, did, nm, x)
                    if r:
                        rows.append(r)
        K.log('%s %s 对照分布完成' % (pname, p))
    od = K.P('diagnostics', 'control_distributions')
    os.makedirs(od, exist_ok=True)
    pth = os.path.join(od, '%s.csv' % pname)
    K.atomic_write_csv(pth, pd.DataFrame(rows))
    K.write_receipt('control_dist_%s' % pname, [pth], 'SUCCEEDED', rows=len(rows), paths=NP)
    print(pname, 'control distributions', len(rows), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
