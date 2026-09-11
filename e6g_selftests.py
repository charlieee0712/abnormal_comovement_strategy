#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-e: 构造性锚与自测 (brief §12)。
   每条测试给 (名称, 期望, 实测最大差, 通过与否, 说明)。收益/区间不是 BLOCKER;
   这里只测正确性: 逐位一致、恒等式、端点。
"""
import os, sys, json, time, math
import numpy as np
import pandas as pd
from fractions import Fraction

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6g_core as G
import e6g_desc as GD

ATOL = 1e-10
R = []


def rec(name, ok, maxdiff=None, note='', level='ANCHOR'):
    R.append(dict(test=name, ok=bool(ok), max_diff=(None if maxdiff is None else float(maxdiff)),
                  note=note, level=level))
    print('%-46s %-5s maxdiff=%-12s %s' % (name, 'OK' if ok else 'FAIL',
                                           ('-' if maxdiff is None else '%.3e' % maxdiff), note),
          flush=True)


def md(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    both = np.isfinite(a) & np.isfinite(b)
    nan_mismatch = int((np.isfinite(a) != np.isfinite(b)).sum())
    return (float(np.max(np.abs(a[both] - b[both]))) if both.any() else 0.0), nan_mismatch


def main(pname):
    t0 = time.time()
    S = G.seg(pname, 'legacy_all')
    ctx = GD.GCtx(S)
    E6E = G.E6E_DIR
    led = {}
    for fld in ('gross', 'pos', 'turn', 'net8'):
        fp = os.path.join(E6E, 'daily', 'daily_%s_%s.parquet' % (fld, pname))
        led[fld] = pd.read_parquet(fp) if os.path.exists(fp) else None
    print('段 %s T=%d Nc=%d, 账本字段 %s' % (pname, S.T, S.Nc,
                                            [k for k, v in led.items() if v is not None]),
          flush=True)

    # ---------- 1. 固定展示组 vs E6e 逐日账本 ----------
    built = {}
    for lab, cfg in GD.display_configs():
        cid = cfg['config_id']
        pnl, iv, mk = ctx.run(cfg)
        built[lab] = (cid, pnl, iv, mk)
        worst, nanmis = 0.0, 0
        seen = []
        for j, fld in enumerate(('gross', 'pos', 'turn')):
            L = led[fld]
            if L is None or cid not in L.columns:
                continue
            d, nm = md(pnl[j], L[cid].to_numpy(float))
            worst = max(worst, d)
            nanmis += nm
            seen.append(fld)
        # net8 不单独存, 由账本 gross/turn 推 (E6e daily/ 只有三个字段)
        if led['gross'] is not None and led['turn'] is not None and cid in led['gross'].columns:
            n8 = (led['gross'][cid].to_numpy(float)
                  - led['turn'][cid].to_numpy(float) * F.COST / 1e4)
            d, nm = md(pnl[3], n8)
            worst = max(worst, d)
            nanmis += nm
            seen.append('net8(derived)')
        rec('A1_ledger_%s[%s]' % (lab, cid), worst <= ATOL and nanmis == 0, worst,
            '字段 %s; NaN 位不一致 %d' % (','.join(seen) or 'NONE_IN_LEDGER', nanmis))

    # ---------- 2. interior_nopos ----------
    for lab in ('R1', 'R2', 'A06', 'A08'):
        inp, lead = GD.interior_nopos(built[lab][1][1])
        rec('A2_interior_nopos_%s' % lab, inp == 0, inp,
            '段内零仓位 %d 天, 段首连续 %d 天' % (inp, lead))

    # ---------- 3. QEDGE == SRC (共同可运行日) ----------
    sc_ktc = ctx.build_core_g(GD.parse_core('KTC_mean@25'))[1]
    for dep in (25, 30, 45, 55):
        g = F.P2G[dep]
        msrc = G.keep_SRC(sc_ktc, S.p0c, dep)
        mq = G.keep_QEDGE(sc_ktc, S.p0c, dep)
        nval = np.array([int((S.p0c[t] & ~np.isnan(sc_ktc[t])).sum()) for t in range(S.T)])
        common = nval >= 3 * g
        diff = int((msrc[common] != mq[common]).sum())
        extra = int(mq[~common].sum())
        rec('A3_QEDGE_eq_SRC_d%d' % dep, diff == 0, diff,
            'g=%d 共同可运行日 %d/%d 逐位差 %d; QEDGE 在非共同日多给 %d 格'
            % (g, int(common.sum()), S.T, diff, extra))

    # ---------- 4. alpha=1/3 三腿加权 == KTC_mean 源构造 ----------
    for dep in (25, 30):
        base = GD.parse_core('KTC_mean@%d' % dep)
        w = GD.mk_core_g('KTC_mean', 'mean', s=dep, keys=[K.FK, K.FT, K.FC],
                         ws=[Fraction(1, 3)] * 3)
        m0, s0, _ = ctx.build_core_g(base)
        m1, s1, _ = ctx.build_core_g(w)
        d, nm = md(s0, s1)
        # 锚的内容是【域一致 + 分数在浮点末位内一致】。wcombine_dense 算 Sum(w*P)/Sum(w),
        # combine_dense 算 nanmean, 数学恒等、末位差 1 ULP -> 恰在分箱边界的票会翻组。
        rec('A4_alpha13_domain_eq_KTCmean@%d' % dep, nm == 0, nm, 'NaN 位必须逐位相同')
        rec('A4_alpha13_score_ulp@%d' % dep, d <= 1e-15, d, '分数差必须在 1 ULP 量级内')
        nd = int((m0 != m1).sum())
        n0, n1 = F.dev_from_dense(S, m0), F.dev_from_dense(S, m1)
        p0_, p1_ = (F.sparse_pnl_H(S, *n0, K.HOLD, F.COST),
                    F.sparse_pnl_H(S, *n1, K.HOLD, F.COST))
        rec('A4_alpha13_boundary_flip@%d' % dep, True, nd,
            '边界翻组 %d / %d 格 (%.4f%%), net8 年化差 %.4f 点'
            % (nd, int(m0.sum()), 100.0 * nd / max(1, int(m0.sum())),
               G.ann(p1_[3]) - G.ann(p0_[3])), level='INFO')

    # ---------- 5. alpha=0 端点 == 真实剔除第四腿 ----------
    for J in ('cum_intraday_ret_5d', 'realized_vol_20d'):
        w0 = GD.mk_core_g('KTC_mean', 'mean', s=25, keys=[K.FK, K.FT, K.FC, J],
                          ws=[Fraction(1, 3)] * 3 + [Fraction(0)])
        m0, s0, _ = ctx.build_core_g(GD.parse_core('KTC_mean@25'))
        m1, s1, _ = ctx.build_core_g(w0)
        d, nm = md(s0, s1)
        # 锚的内容: 零权重分量【不能改变有效域】。J 的缺失格若泄漏进来, NaN 位会不同。
        rec('A5_alpha0_bypass_domain_%s' % J, nm == 0, nm,
            'J 的缺失不得剔股: NaN 位差必须为 0')
        rec('A5_alpha0_bypass_score_%s' % J, d <= 1e-15, d, '分数差在 1 ULP 量级内')
        rec('A5_alpha0_boundary_flip_%s' % J, True, int((m0 != m1).sum()),
            '边界翻组格数 (同 A4, 非经济效应)', level='INFO')

    # ---------- 6. H2 变换端点 ----------
    spT = D.DT_
    raw = G.build_raw_g(S, spT)
    d, _ = md(G.tf_apply(raw, 'identity').values, raw.values)
    rec('A6_tf_identity', d == 0.0, d, 'identity 必须逐位等于原值')
    const = pd.DataFrame(np.full(raw.shape, 3.5), index=raw.index, columns=raw.columns)
    for kk in ('delta5', 'delta20'):
        v = G.tf_apply(const, kk).values
        fin = np.isfinite(v)
        rec('A6_tf_%s_const_zero' % kk, bool(np.all(v[fin] == 0.0)),
            float(np.max(np.abs(v[fin]))) if fin.any() else 0.0, '常数序列的非零 lag 差分 = 0')
    z1 = G.tf_apply(raw, 'zprior60').values
    zs = G.tf_apply(raw * 7.0, 'zprior60').values           # 纯缩放
    za = G.tf_apply(raw * 7.0 + 3.0, 'zprior60').values     # 缩放 + 大平移
    d1, nm1 = md(z1, zs)
    d2, nm2 = md(z1, za)
    sc = float(np.nanmedian(np.abs(raw.values)))
    fin = np.isfinite(z1) & np.isfinite(zs)
    rel = float(np.max(np.abs(z1[fin] - zs[fin]) / np.maximum(1e-12, np.abs(z1[fin]))))
    inp = fin & S.p0
    dpool = float(np.max(np.abs(z1[inp] - zs[inp]))) if inp.any() else 0.0
    zmax = float(np.max(np.abs(z1[fin])))
    rec('A6_tf_z_scale_invariant_rel', rel <= 1e-5 and nm1 == 0, rel,
        '缩放不变性按【相对】差判: pandas rolling.std 在近退化窗上有条件数损失')
    rec('A6_tf_z_scale_invariant_pool_abs', dpool <= 1e-5, dpool,
        '池内格 (H2 唯一实际用到的格) 的绝对差')
    rec('A6_tf_z_extreme_window', True, zmax,
        '全网格最大 |z| = %.4g; 绝对差集中在 |z| >> 1 的近常数历史窗 (全网格最大绝对差 %.3e)'
        % (zmax, d1), level='INFO')
    rec('A6_tf_z_shift_conditioning', True, d2,
        'z 对【大平移】的差 %.3e: rolling.std 的条件数损失, 不是逻辑错 '
        '(原值中位量级 %.3g, 平移 +3 = %.0f 倍); 本轮 z 只施于原始因子, 不做平移'
        % (d2, sc, 3.0 / max(sc, 1e-12)), level='INFO')
    zc = G.tf_apply(const, 'zprior60').values
    rec('A6_tf_z_const_undefined', bool(np.all(~np.isfinite(zc))), None,
        '历史常数 -> std=0 -> z 无定义 (全 NaN)')
    pert = raw.copy()
    cut = int(S.T * 0.6)
    pert.iloc[cut:, :] = pert.iloc[cut:, :] + 1000.0
    for kk in ('delta5', 'delta20', 'zprior60'):
        a = G.tf_apply(raw, kk).values[:cut - 20]
        b = G.tf_apply(pert, kk).values[:cut - 20]
        d, nm = md(a, b)
        rec('A6_tf_%s_no_lookahead' % kk, d == 0.0 and nm == 0, d, '未来扰动不影响过去前缀')

    # ---------- 7. 方向: 真实反序 vs 1-pct ----------
    Phi = G.get_pct_g(S, spT, 'NS', 'hi', 'identity')
    Plo = G.get_pct_g(S, spT, 'NS', 'lo', 'identity')
    approx = 1.0 - Phi
    d, nm = md(Plo, approx)
    nval = np.array([int((S.p0c[t] & ~np.isnan(Phi[t])).sum()) for t in range(S.T)])
    rec('A7_reverse_vs_1minus_pct', True, d,
        '不是恒等式, 只登记: 最大差 %.3e, 差 >1e-12 的格 %d, 有值池中位 %d 只'
        % (d, int((np.abs(Plo - approx) > 1e-12).sum()), int(np.median(nval))), level='INFO')
    # 差的来源: 对 average 并列法, (-s).rank(pct) = 1 + 1/n - s.rank(pct) -> 逐日常数偏移 1/n。
    off = np.full(S.T, np.nan)
    for t in range(S.T):
        v = S.p0c[t] & np.isfinite(Phi[t]) & np.isfinite(Plo[t])
        if v.sum() >= 2:
            off[t] = np.nanmax(np.abs((Plo[t, v] + Phi[t, v]) - (1.0 + 1.0 / v.sum())))
    rec('A7_reverse_offset_is_1_over_n', float(np.nanmax(off)) <= 1e-12, float(np.nanmax(off)),
        '(-s).rank(pct) + s.rank(pct) 必须恒等于 1 + 1/n (平局用 average 法)')
    # 单腿掩码不受影响 (同序), 多腿均值会受影响 -> 这正是"不许默认 1-pct"的原因
    ms_lo = G.keep_SRC(Plo, S.p0c, 25)
    ms_ap = G.keep_SRC(approx, S.p0c, 25)
    rec('A7_reverse_same_order_single_leg', bool((ms_lo == ms_ap).all()),
        int((ms_lo != ms_ap).sum()), '单腿: 真实反序与 1-pct 同序 -> 掩码逐位相同')

    # ---------- 8. 四腿 trimmed_mean == median ----------
    rng = np.random.default_rng(7)
    X = rng.random((4, 500))
    X[:, :20] = np.nan
    tm = np.sort(X, axis=0)[1:3].mean(axis=0)
    me = np.median(X, axis=0)
    d, nm = md(tm, me)
    rec('A8_trimmed4_eq_median4', d <= 1e-15 and nm == 0, d, '四数去头尾均值 = 中位数 (别名)')

    # ---------- 9. Blend3 gross/pos = 成员平均 ----------
    mem = [built[x][2] for x in G.BLEND3_MEMBERS]
    bi, bv = G.blend3_weights(mem)
    bp = F.sparse_pnl_H(S, bi, bv, K.HOLD, F.COST)
    for j, fld in enumerate(('gross', 'pos')):
        avg = np.mean([built[x][1][j] for x in G.BLEND3_MEMBERS], axis=0)
        d, nm = md(bp[j], avg)
        rec('A9_blend3_%s_eq_member_mean' % fld, d <= 1e-12 and nm == 0, d,
            'Blend3 的 %s 必须等于成员平均' % fld)
    dturn, _ = md(bp[2], np.mean([built[x][1][2] for x in G.BLEND3_MEMBERS], axis=0))
    rec('A9_blend3_turn_not_mean', True, dturn,
        'turn 必须合并后重算, 与成员平均的差 = %.4f (期望 > 0)' % dturn, level='INFO')

    # ---------- 10. 引擎 H=5 == e6e sparse_pnl ----------
    idx, val = built['R2'][2]
    p5 = F.sparse_pnl_H(S, idx, val, 5, F.COST)
    S.den = S.den5                        # e6e.sparse_pnl 读 S.den, e6f.build_segment 写 S.den5
    pe = K.sparse_pnl(S, idx, val, F.COST)
    worst = 0.0
    for j in range(4):
        d, _ = md(p5[j], pe[j])
        worst = max(worst, d)
    rec('A10_engine_H5_eq_e6e', worst == 0.0, worst, 'sparse_pnl_H(H=5) 必须与 e6e sparse_pnl 逐位相同')

    # ---------- 11. 基准全 NaN 日 ----------
    nb = int(np.isnan(S.bench).sum())
    rec('A11_bench_all_nan_days', nb == 19, abs(nb - 19), '本段 %d 天 (四段合计应为 76)' % nb)

    # ---------- 12. RANKBUDGET 在映射深度上的差异 (只登记) ----------
    for dep in (25, 30):
        msrc = G.keep_SRC(sc_ktc, S.p0c, dep)
        mrb = G.keep_RANKBUDGET(sc_ktc, S.p0c, dep)
        rec('A12_RANKBUDGET_vs_SRC_d%d' % dep, True, int((msrc != mrb).sum()),
            '人数 SRC %.1f / RB %.1f' % (msrc.sum(1).mean(), mrb.sum(1).mean()), level='INFO')

    out = os.path.join(G.RES, 'checks')
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'selftests_%s.json' % pname), 'w') as fh:
        json.dump(dict(segment=pname, results=R, elapsed_s=round(time.time() - t0, 1)),
                  fh, indent=1, ensure_ascii=False)
    anch = [r for r in R if r['level'] == 'ANCHOR']
    nb_ = sum(1 for r in anch if not r['ok'])
    print('\n[%s] 锚 %d/%d 通过 (另 %d 条只登记), %.0fs'
          % (pname, len(anch) - nb_, len(anch), len(R) - len(anch), time.time() - t0))
    return nb_


if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1]) else 0)
