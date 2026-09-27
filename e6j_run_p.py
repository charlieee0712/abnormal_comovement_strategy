# -*- coding: utf-8 -*-
"""E6j P 块（冻结五臂试点）原生账户 + 同资本 + 冲击括号 + 目标统计 + 掩码（brief v1.2 §6；plan §4 / §7）。
一段一个进程（--segment），逐形态一个任务回执。登记门：`registration/P_package_manifest.json` 必须存在且 registry sha 与之一致，
否则拒绝计算任何登记对象（--profile 模式只算 C0 母体与"复制旧坏度作 NEW"的无新增批次，用于测时，不读新对象收益）。
存储：accounts/P/<段>/<形态>.npz（描述符 × 交易日：gross / pos / turn / net8 / 同资本子 / 同资本母 / 冲击括号 / 未定价换手 /
目标只数 / 目标权重和）+ masks_<形态>.npz（22 个掩码的单元位图）；汇总 CSV 另写。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL
import e6j_engine as EN

OUT = os.path.join(J.RES, 'accounts', 'P')
ALPHAS = (0.125, 0.25, 0.5)
HS = EN.HS_P
MEMBERS = {'S': ('K_rar20', 'lo'), 'M': ('K_slope20', 'lo'), 'C1': ('K_MA3_E6F', 'hi'), 'K_rarpre': ('K_rarpre', 'lo'),
           'K_samt20': ('K_samt20', 'lo'), 'A5': ('K_amt5', 'lo'), 'S5': ('K_samt5', 'lo'), 'A20': ('K_amt20', 'lo')}
OBJECTS = [  # (arm 键, 描述符里的 arm / member / direction, 分量)
    ('S', 'S', 'K_rar20', 'low_bad', [(1.0, 'S')]),
    ('M', 'M', 'K_slope20', 'low_bad', [(1.0, 'M')]),
    ('SM', 'SM', 'K_rar20+K_slope20', 'low_bad+low_bad', [(0.5, 'S'), (0.5, 'M')]),
    ('C1', 'C1', 'K_MA3_E6F', 'high_bad', [(1.0, 'C1')]),
    ('COL:K_rarpre', 'COL', 'K_rarpre', 'low_bad', [(1.0, 'K_rarpre')]),
    ('COL:K_samt20', 'COL', 'K_samt20', 'low_bad', [(1.0, 'K_samt20')]),
    ('COL:AMT4', 'COL', 'AMT4', 'low_bad×4', [(0.25, 'A5'), (0.25, 'S5'), (0.25, 'A20'), (0.25, 'K_samt20')]),
]


def desc_id(form, arm, member, d, a, H):
    if arm == 'C0':
        return 'P|%s|C0|-|-|a=0|H%d' % (form, H)
    if arm == 'COL':
        return 'P|%s|COL|%s|%s|a=%s|H%d' % (form, member, d, a, H)
    return 'P|%s|%s|%s|%s|a=%s|H%d' % (form, arm, member, d, a, H)


def registration_ok():
    p = os.path.join(J.RES, 'registration', 'P_package_manifest.json')
    if not os.path.exists(p):
        return False, 'P 包未登记'
    m = json.load(open(p))
    for f, s in m['registry_sha256'].items():
        if J.sha_file(os.path.join(J.RES, 'registry', f)) != s:
            return False, 'registry/%s 与登记时 sha 不同' % f
    return True, m['written_at']


def size_pct_cells(env):
    """clean 域流通市值百分位（逐日，[0,1]），取 pool0 单元。"""
    S = env.S
    mc = S.data['mcap'].astype(float).reindex(index=S.pool0.index, columns=S.pool0.columns)
    cl = S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0) == 1
    pct = mc.where(cl).rank(axis=1, pct=True).values[:, S.ccols]
    return pct[env.ci.t, env.ci.c]


def size_gap(env, kept_child, kept_parent, szc):
    """形成日换入 / 换出的 clean 域市值百分位中位差 gap_t（只在两边都有且市值已知的日子）；返回 (mean gap, mean |gap|, 两边日数, 单边日数)。"""
    ci = env.ci
    ent = kept_child & ~kept_parent; ext = kept_parent & ~kept_child
    gaps, one = [], 0
    for t in np.unique(ci.t[ent | ext]):
        sl = ci.t == t
        e = szc[sl & ent]; x = szc[sl & ext]
        e = e[np.isfinite(e)]; x = x[np.isfinite(x)]
        if len(e) and len(x):
            gaps.append(np.median(e) - np.median(x))
        else:
            one += 1
    g = np.array(gaps)
    return (float(g.mean()) if len(g) else np.nan, float(np.abs(g).mean()) if len(g) else np.nan, len(g), one)


def run(pname, profile=False):
    t0 = time.time()
    log = os.path.join(J.RES, 'logs', 'run_p_%s%s.log' % (pname, '_profile' if profile else ''))
    ok, why = registration_ok()
    if not profile and not ok:
        raise RuntimeError('登记门：%s（先运行 e6j_prereg.py）' % why)
    env = EN.Env(pname, with_prod=True)
    import e6g_c as GC
    mkt = GC.MarketCtx(env.S)
    ctx, ci, SE = env.ctx, env.ci, env.SE
    T = env.S.T
    szc = size_pct_cells(env)
    if profile:
        mem = {}
    else:
        mem = {k: env._dense_cells(SL.member_pct(ctx, mid, d)[0]) for k, (mid, d) in MEMBERS.items()}
    J.log('%s env ready %.0fs (profile=%s)' % (pname, time.time() - t0, profile), log)
    os.makedirs(os.path.join(OUT, pname), exist_ok=True)
    summ = []
    for form in P.DELIV:
        tf = time.time()
        st = EN.prod_structure(env, form)
        rows, Q = [('C0', 'C0', '-', '-', 0.0)], [st.q0]
        if profile:                                      # 无新增批次：复制旧坏度作 NEW（逐位回到母体），只为测时
            for a in ALPHAS:
                for k in range(len(OBJECTS)):
                    rows.append(('COPY%d' % k, 'COPY', 'q0', '-', a)); Q.append(EN.blend(st.q0, [(1.0, st.q0[None, :])], a)[0])
        else:
            for key, arm, member, d, parts in OBJECTS:
                for a in ALPHAS:
                    rows.append((key, arm, member, d, a))
                    Q.append(EN.blend(st.q0, [(sh, mem[m][None, :]) for sh, m in parts], a)[0])
        kept = st.kept(np.vstack([q[None, :] for q in Q]))
        # 母体（C0）目标
        k0 = kept[0]; t_b, c_b = ci.t[k0], ci.c[k0]; w_b = SE.dev(t_b, c_b)
        pb = np.bincount(t_b, weights=w_b, minlength=T)
        ids, arrs = [], {k: [] for k in ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss', 'nnames', 'wsum')}
        for j, (key, arm, member, d, a) in enumerate(rows):
            kj = kept[j]; t, c = ci.t[kj], ci.c[kj]; w = SE.dev(t, c)
            led = SE.pnl(t, c, w, HS, 8.0)
            pc = np.bincount(t, weights=w, minlength=T)
            ps = np.minimum(pc, pb)
            with np.errstate(divide='ignore', invalid='ignore'):
                fc = np.where(pc > 0, ps / pc, 0.0); fb = np.where(pb > 0, ps / pb, 0.0)
            scc = SE.pnl(t, c, w * fc[t], HS, 8.0); scb = SE.pnl(t_b, c_b, w_b * fb[t_b], HS, 8.0)
            idx = [c[t == d_] for d_ in range(T)]; val = [w[t == d_] for d_ in range(T)]
            gap = size_gap(env, kj, k0, szc) if j > 0 else (np.nan, np.nan, 0, 0)
            for H in HS:
                g, pos, tu, n = led[H]
                br = GC.profile_and_impact(mkt, idx, val, H, full_profile=False)
                ids.append(desc_id(form, arm, member, d, a, H))
                arrs['gross'].append(g); arrs['pos'].append(pos); arrs['turn'].append(tu); arrs['net8'].append(n)
                arrs['sc_child'].append(scc[H][3]); arrs['sc_parent'].append(scb[H][3])
                arrs['bracket'].append(br[0]['sqrt']); arrs['qmiss'].append(br[3])
                arrs['nnames'].append(np.bincount(t, minlength=T).astype(float)); arrs['wsum'].append(pc)
                summ.append(dict(segment=pname, descriptor_id=ids[-1], form=form, arm=key, alpha=a, H=H,
                                 net8_ann=float(np.nanmean(n)) * J.ANN, gross_ann=float(np.nanmean(g)) * J.ANN,
                                 turn_mean=float(np.mean(tu)), pos_mean=float(np.mean(pos)), n_target_mean=float(len(t) / T),
                                 matched_capital_share=float(ps.sum() / pc.sum()) if pc.sum() > 0 else np.nan,
                                 size_gap_mean=gap[0], size_gap_absmean=gap[1], size_gap_days=gap[2], size_onesided_days=gap[3],
                                 n_mask_cells=int(kj.sum())))
        path = os.path.join(OUT, pname, '%s%s.npz' % (form, '_profile' if profile else ''))
        J.atomic_write_npz(path, desc=np.array(ids), dates=np.array([str(d)[:10] for d in env.dates]),
                           **{k: np.vstack(v) for k, v in arrs.items()})
        mpath = os.path.join(OUT, pname, 'masks_%s%s.npz' % (form, '_profile' if profile else ''))
        J.atomic_write_npz(mpath, rows=np.array(['%s|%s' % (r[0], r[4]) for r in rows]), bits=np.packbits(kept, axis=1), n=np.array([ci.n]))
        if not profile:
            J.write_receipt('run_p_%s_%s' % (pname, form), [path, mpath], 'SUCCEEDED', n_desc=len(ids))
        J.log('  %s %s: %d 描述符 %.0fs' % (pname, form, len(ids), time.time() - tf), log)
    sp = os.path.join(OUT, pname, 'summary%s.csv' % ('_profile' if profile else ''))
    J.atomic_write_csv(sp, pd.DataFrame(summ))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
    J.log('%s done %.0fs maxrss %.1f GB' % (pname, time.time() - t0, rss), log)
    return 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[sys.argv.index('--segment') + 1], profile='--profile' in sys.argv))
