# -*- coding: utf-8 -*-
"""E6k Stage 0 第 2 类：源账户（brief §2 第 2 类；附录 A2-1 … A2-5、A2-7；A2-6 随机复现归第 5 类）。
  --prod            A2-1 六形态 α = 0 逐段重跑 export_delivery_pools_v2 流水线 → 六个 pool2 + pool1 逐字节 = E5a；
                    A2-2 summary.csv（6bp）逐字节 + 逐列数值；8bp 日账本恒等 net8 − net6 = −2e−4·turn（1e−12）与年化精确式
                    net8 = net6 − 0.02·turn·L/n（1e−9）；母体生产日账本写 anchors/ 并与 E6j anchors/mother_ledger_prod_v2.parquet 逐列逐位比对
  --segment S       E6k 引擎（e6k_env / e6k_acct，稀疏账本）：
                    A2-3 R2 / A06 母体 H5 net8 日账本 = E6i 已存母体日账本（net8 − dnet8；E6j anchor2 口径）
                    A2-4 原生 S / M / C1 / SM 主配置（六形态 × α .25 × H5）= E6j accounts/P 同描述符 gross / pos / turn / net8 /
                         sc_child / sc_parent / bracket / qmiss 逐日（1e−12，NaN 位置一致）
                    A2-5 Q（J_B1_qCC low_bad）与四个 RARPRE 源对象在 A4b_CVRv5(= R1) / R2 / A06 × α .25 × H5 = E6j accounts/B 同 ID
                    A2-7 六形态母体 H5 8bp 年化 = E6j carried/leader_six_forms_capital.csv total_net8_ann（1e−9）
只读 E5a / E6i / E6j；只写 E6k 结果目录。"""
import e6k_boot  # noqa: F401
import os
import sys
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6k_core as K

TOL_DAILY = 1e-12
TOL_ANN = 1e-9
EPS = np.finfo(np.float64).eps


def fcmp(a, b):
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    na, nb = np.isnan(a), np.isnan(b)
    m = ~(na | nb)
    d = np.abs(a[m] - b[m]) if m.any() else np.zeros(1)
    return bool((na == nb).all()), float(d.max())


def prod(out, rerun):
    import e6j_prod as PR
    import comprehensive_factor_diagnosis as C
    rows, rows6, rows8, stats = [], [], [], []

    def chk(cid, obj, metric, expected, got, ok, note='', gate=True):
        st = 'INFO' if ok is None else ('PASS' if ok else ('FAIL' if gate else 'DIFFERS'))
        rows.append(dict(check_id=cid, object=obj, metric=metric, expected=str(expected), got=str(got), status=st, note=note))
    e5a = {f: K.sha_file(os.path.join(K.E5A_RES, f)) for f in ['summary.csv', 'pool1_I11_screening.csv'] +
           ['pool2_%s.csv' % PR.FNAME[c] for c in PR.DELIV]}
    pool1_parts, pool2_parts, ledgers, prof = [], {c: [] for c in PR.DELIV}, [], []
    for pname in PR.SEGS:
        t0 = time.time()
        ctx = PR.build_period(pname)
        t1 = time.time()
        masks = PR.form_masks(ctx)
        w_pool, pr_pool6, bm2 = PR.pool_bench(ctx, 6.0)
        pool1_parts.append(PR.pool1_part(ctx))
        for cfg in PR.DELIV:
            hold, w = PR.weights_of(ctx, masks[cfg])
            pr6 = C.compute_calendar_pnl(w, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=6.0)
            r6, net2_6 = PR.summary_row(pname, cfg, hold, w, pr6, bm2, 6.0)
            pr8 = C.compute_calendar_pnl(w, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=8.0)
            r8, net2_8 = PR.summary_row(pname, cfg, hold, w, pr8, bm2, 8.0)
            rows6.append(r6)
            rows8.append(r8)
            obj = '%s|%s' % (pname, cfg)
            for key in ('gross_excess_daily', 'port_daily', 'bench_daily', 'daily_position', 'daily_turnover'):
                sn, md = fcmp(pr6[key].values, pr8[key].values)
                chk('A2-2', obj, '%s 6bp ≡ 8bp' % key, 0.0, md, sn and md == 0.0)
            resid = (pr8['net_excess_daily'] - pr6['net_excess_daily'] + 2e-4 * pr8['daily_turnover'])
            md = float(np.nanmax(np.abs(resid.values))) if resid.notna().any() else 0.0
            chk('A2-2', obj, '逐日 net8 − net6 + 2e−4·turn', 0.0, md, md <= TOL_DAILY)
            L = len(pr8['daily_turnover'])
            nn = int(r8['n'])
            hd = float(pr8['daily_turnover'][pr8['net_excess_daily'].isna()].sum())
            exact = r6['net_ann'] - 0.02 * r6['turn'] * L / nn
            chk('A2-2', obj, '年化 net8 = net6 − 0.02·turn·L/n（缺失日换手 = 0）', exact, r8['net_ann'], abs(r8['net_ann'] - exact) <= TOL_ANN and hd == 0.0,
                'L=%d n=%d' % (L, nn))
            idx = pr6['gross_excess_daily'].index
            ledgers.append(pd.DataFrame({'period': pname, 'cfg': cfg, 'date': [pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in idx],
                                         'port_daily': pr8['port_daily'].values, 'bench_daily': pr8['bench_daily'].values,
                                         'daily_position': pr8['daily_position'].values, 'daily_turnover': pr8['daily_turnover'].values,
                                         'gross_excess': pr8['gross_excess_daily'].values, 'net6': pr6['net_excess_daily'].values,
                                         'net8': pr8['net_excess_daily'].values}))
            pool2_parts[cfg].append(PR.pool2_part(ctx, w))
        prof.append(dict(period=pname, load_s=round(t1 - t0, 1), forms_s=round(time.time() - t1, 1),
                         maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0, 2)))
        del ctx, masks
    for cfg in PR.DELIV:
        fn = 'pool2_%s.csv' % PR.FNAME[cfg]
        b, dfp = PR.pool2_bytes(pool2_parts[cfg])
        s = K.sha_bytes(b)
        stats.append(dict(cfg=cfg, rows=len(dfp)))
        chk('A2-1', fn, 'sha256 逐字节 = E5a', e5a[fn], s, s == e5a[fn], 'rows=%d' % len(dfp))
    b1, _ = PR.pool1_bytes(pool1_parts)
    chk('A2-1', 'pool1_I11_screening.csv', 'sha256 逐字节 = E5a', e5a['pool1_I11_screening.csv'], K.sha_bytes(b1),
        K.sha_bytes(b1) == e5a['pool1_I11_screening.csv'])
    s6 = pd.DataFrame(rows6)
    b = s6.to_csv(index=False).encode('utf-8')
    chk('A2-2', 'summary.csv', 'sha256 逐字节 = E5a（6bp）', e5a['summary.csv'], K.sha_bytes(b), K.sha_bytes(b) == e5a['summary.csv'])
    ref = pd.read_csv(os.path.join(K.E5A_RES, 'summary.csv'), float_precision='round_trip')
    for col in ref.columns[2:]:
        d = float(np.nanmax(np.abs(ref[col].values.astype(float) - s6[col].values.astype(float))))
        chk('A2-2', 'summary.csv', '列 %s max|Δ|' % col, 0.0, d, d == 0.0)
    led = pd.concat(ledgers, ignore_index=True)
    old = pd.read_parquet(os.path.join(K.E6J_RES, 'anchors', 'mother_ledger_prod_v2.parquet'))
    old = old[old.cfg != 'POOL0_DEV'][list(led.columns)].reset_index(drop=True)
    same = len(old) == len(led)
    if same:
        for col in led.columns:
            a_, b_ = old[col].values, led[col].values
            same &= bool(np.array_equal(a_.astype(float), b_.astype(float), equal_nan=True)) if led[col].dtype.kind == 'f' \
                else bool((a_.astype(str) == b_.astype(str)).all())
    chk('A2-2', 'E6j anchors/mother_ledger_prod_v2.parquet', '六形态母体 6 / 8bp 日账本逐列逐位', True, same, same)
    os.makedirs(K.P('anchors'), exist_ok=True)
    lp = K.P('anchors', 'mother_ledger_prod_v2_E6k.parquet')
    tmp = lp + '.tmp.%d' % os.getpid()
    led.to_parquet(tmp, index=False)
    os.replace(tmp, lp)
    p8 = K.P('anchors', 'mother_summary_8bp_E6k.csv')
    K.atomic_write_csv(p8, pd.DataFrame(rows8))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'source_prod_checks.csv')
    K.atomic_write_csv(p, df)
    pp = os.path.join(out, 'source_prod_profile.csv')
    K.atomic_write_csv(pp, pd.DataFrame(prof))
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('stage0_c2_source_prod' + ('_rerun' if rerun else ''), [p, pp, lp, p8], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    print(df[df.status != 'PASS'].to_string(max_colwidth=80), flush=True)
    return 0 if ok else 2


def engine(pname, out, rerun):
    import e6k_env as E
    import e6k_ops as O
    import e6k_acct as AC
    import e6j_engine as EN
    import e6j_stage0_parent_identity as PI
    t0 = time.time()
    seg = E.Seg(pname)
    acct = AC.Acct(seg)
    rows = []

    def chk(cid, obj, metric, expected, got, ok, note=''):
        rows.append(dict(check_id=cid, segment=pname, object=obj, metric=metric, expected=str(expected), got=str(got),
                         status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), note=note))

    def cmp_arrays(cid, obj, mine, ref_z, row, keys):
        for k in keys:
            if k not in ref_z.files:
                continue
            sn, md = fcmp(mine[k], ref_z[k][row])
            chk(cid, obj, '%s 逐日（NaN 位置一致）' % k, '≤ %g' % TOL_DAILY, '%.3e' % md, sn and md <= TOL_DAILY)
    # A2-3 R2 / A06
    for mn in ('R2', 'A06'):
        st = seg.struct(mn)
        par = st.kept(st.q0[None, :])[0]
        tg = acct.target(par)
        led = acct.ledgers(tg, (5,), impact=False, roll=False)[5]
        ref = PI.e6i_parent_ledger(pname, mn)
        both = np.isfinite(ref['parent'])
        sn, md = fcmp(np.where(both, led['net8'], np.nan), ref['parent'])
        chk('A2-3', mn, 'H5 net8 日账本 vs E6i 已存母体（%s）' % ref['descriptor_id'], '≤ 1e−12（稀疏 vs 稠密）', '%.3e' % md, sn and md <= TOL_DAILY)
        ann = float(np.nanmean(led['net8'])) * K.ANN
        chk('A2-3', mn, 'net8 年化 vs E6i parent_net8_ann', ref['parent_net8_ann'], ann, abs(ann - ref['parent_net8_ann']) <= TOL_ANN)
        chk('A2-3', mn, 'parent_n_mean vs E6i', ref['parent_n_mean'], float(par.sum() / seg.T), abs(par.sum() / seg.T - ref['parent_n_mean']) <= 1e-9)
    # A2-4 / A2-7 六形态
    zP = {}
    lead = pd.read_csv(os.path.join(K.E6J_RES, 'carried', 'leader_six_forms_capital.csv'))
    keys = ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss')
    for form in E.P6:
        st = seg.struct(form)
        k0 = st.q0
        par = st.kept(k0[None, :])[0]
        tp = acct.target(par)
        lp = acct.ledgers(tp, (5,), impact=False, roll=False)[5]
        ann = float(np.nanmean(lp['net8'])) * K.ANN
        ref = float(lead[(lead.segment == pname) & (lead.form == form)].total_net8_ann.iloc[0])
        chk('A2-7', form, '母体 H5 8bp 年化 = E6j 领导表 total_net8_ann', ref, ann, abs(ann - ref) <= TOL_ANN)
        z = zP[form] = np.load(os.path.join(K.E6J_RES, 'accounts', 'P', pname, '%s.npz' % form), allow_pickle=False)
        desc = list(z['desc'])
        for arm, member, d, parts in (('S', 'K_rar20', 'low_bad', [(1.0, 'S')]), ('M', 'K_slope20', 'low_bad', [(1.0, 'M')]),
                                      ('C1', 'K_MA3_E6F', 'high_bad', [(1.0, 'C1')]),
                                      ('SM', 'K_rar20+K_slope20', 'low_bad+low_bad', [(0.5, 'S'), (0.5, 'M')])):
            did = 'P|%s|%s|%s|%s|a=%s|H%d' % (form, arm, member, d, 0.25, 5)
            row = desc.index(did)
            if len(parts) == 1:
                q = O.native_q(k0, seg.kf(parts[0][1]), 0.25)
            else:
                q = EN.blend(k0, [(sh, seg.kf(m)[None, :]) for sh, m in parts], 0.25)[0]
            kept = st.kept(q[None, :])[0]
            tg = acct.target(kept)
            led = acct.ledgers(tg, (5,), par=tp, roll=False)[5]
            cmp_arrays('A2-4', '%s|%s' % (form, arm), led, z, row, keys)
    # A2-5 Q / RARPRE on R1(= A4b_CVRv5) / R2 / A06
    for mn, e6j_m in (('A4b_CVRv5', 'R1'), ('R2', 'R2'), ('A06', 'A06')):
        st = seg.struct(mn)
        k0 = st.q0
        par = st.kept(k0[None, :])[0]
        tp = acct.target(par)
        for meas, blk in (('Q', 'B1'), ('RARPRE20_LT', 'B5'), ('RARPRE60_LT', 'B5'), ('RARPRE20_SE', 'B5'), ('RARPRE60_SE', 'B5')):
            mid = E.MEAS[meas][1]
            zb = np.load(os.path.join(K.E6J_RES, 'accounts', 'B', pname, '%s__%s.npz' % (e6j_m, blk)), allow_pickle=False)
            did = 'B|%s|%s|K|%s|low_bad|FALLBACK|a=0.25|H5' % (blk, e6j_m, mid)
            desc = list(zb['desc'])
            if did not in desc:
                chk('A2-5', '%s|%s' % (mn, meas), 'E6j 描述符存在', did, 'MISSING', False)
                continue
            row = desc.index(did)
            q = O.native_q(k0, seg.kf(meas), 0.25)
            kept = st.kept(q[None, :])[0]
            tg = acct.target(kept)
            led = acct.ledgers(tg, (5,), par=tp, roll=False)[5]
            cmp_arrays('A2-5', '%s|%s' % (mn, meas), led, zb, row, keys)
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'source_engine_%s.csv' % pname)
    K.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('stage0_c2_source_engine_%s%s' % (pname, '_rerun' if rerun else ''), [p], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok, wall_s=round(time.time() - t0, 1),
                    maxrss_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0, 2))
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', 'wall %.0fs' % (time.time() - t0), flush=True)
    print(df[df.status != 'PASS'].to_string(max_colwidth=80), flush=True)
    return 0 if ok else 2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prod', action='store_true')
    ap.add_argument('--segment', default=None)
    ap.add_argument('--rerun', action='store_true')
    a = ap.parse_args()
    out = K.P('stage0', 'c2_source' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    if a.prod:
        return prod(out, a.rerun)
    return engine(a.segment, out, a.rerun)


if __name__ == '__main__':
    sys.exit(main())
