# -*- coding: utf-8 -*-
"""E6j Stage 0 锚 1（brief v1.2 §2 第 1 项、W02 / W04）：生产路径恒等锚。
α = 0（源父）逐段重跑 export_delivery_pools_v2 的六形态：
  ① 六个 pool2 文件逐字节（行 / 日期 / ticker / weight，'%.8g'，tradeDate→ticker 排序）= E5a；
  ② summary.csv 全列（6bp）逐字节 + 逐列数值差；附带 pool1、_delivery_stats.csv、check.csv 逐字节；
  ③ 同一冻结权重 cost_bp_bilateral=8 重算：gross / 持仓 / 换手与 6bp 逐位相同，逐日 net8 − net6 = −2e−4 × daily_turnover，
     年化精确式 net8 = net6 − 0.02 × turn × L / n（L = 账本行数、n = 非缺失净值日；缺失日换手须为 0），
     brief 的 "≈ net6 − 0.02 × turn" 残差与 W02 两位小数换算值只作 DIFFERS / INFO 记录、不设门；
  ④ 保存六形态（+ pool0 DEV 副基准）8bp 母体日账本 = 此后一切"子 − 母"的母。
任一形态不一致 → BLOCKER（回执 FAILED，不进入后续锚）。只读 E5a / 源码；只写 E6j 结果目录。
--rerun：首跑回执 FAILED 后的同名重跑（协议 v1.1 ⑤）——检查结果写 stage0/anchor1_rerun/；anchors/ 下已存在的母体账本与
summary 不覆盖，改为与本次重算逐位比对（results 只增不删）。
首跑（00:50）FAILED 的 30 项全是本脚本检查定义错：A1-S3 用 read_csv 默认快速浮点解析（1e−16 级假差；逐字节 A1-S1 已 PASS）、
A1-C3 用近似式配 0.005 容差（定义差 L/n 未计入）、A1-C4 对 brief 两位小数换算值设门；生产口径数字零改动。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import hashlib
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import comprehensive_factor_diagnosis as C

RERUN = '--rerun' in sys.argv
TASK = 'stage0_anchor1_prod_path' + ('_rerun' if RERUN else '')
OUT = os.path.join(J.RES, 'stage0', 'anchor1_rerun' if RERUN else 'anchor1')
ANC = os.path.join(J.RES, 'anchors')
LOG = os.path.join(J.RES, 'logs', TASK + '.log')
SRC_FILES = ['export_delivery_pools_v2.py', 'comprehensive_factor_diagnosis.py', 'data_loader.py', 'features_daily.py',
             'event_study.py', 'pool_screening_v2.py', 'e6j_boot.py', 'e6j_core.py', 'e6j_prod.py', 'e6j_stage0_prod_anchor.py']
W02_NET8_A4B_CVR = {'2010-2014': 2.80, '2015-2018': 6.58, '2019-2023': 7.88, '2024-2026': 9.69}   # brief W02 由 turn 换算（2 位小数）
TOL_DAILY = 1e-12       # 逐日恒等（浮点）
TOL_ANN_EXACT = 1e-9    # 年化精确式 net8 = net6 − 0.02·turn·L/n
TOL_W02 = 0.006         # 与 brief 两位小数换算值的差（只记 DIFFERS，不设门）


def _log(m):
    J.log(m, LOG)


def ledger_frame(pname, cfg, pr6, pr8, bm2, net2_6, net2_8):
    idx = pr6['gross_excess_daily'].index
    return pd.DataFrame({
        'period': pname, 'cfg': cfg,
        'date': [pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in idx],
        'port_daily': pr8['port_daily'].values, 'bench_daily': pr8['bench_daily'].values, 'bm2_daily': bm2.reindex(idx).values,
        'daily_position': pr8['daily_position'].values, 'daily_turnover': pr8['daily_turnover'].values,
        'gross_excess': pr8['gross_excess_daily'].values, 'net6': pr6['net_excess_daily'].values, 'net8': pr8['net_excess_daily'].values,
        'net2_6': net2_6.reindex(idx).values, 'net2_8': net2_8.reindex(idx).values})


def maxabs_nanaware(a, b):
    """两序列逐位比较：NaN 位置须一致；返回 (NaN 位置一致?, 非 NaN 处最大绝对差)。"""
    a = np.asarray(a, float); b = np.asarray(b, float)
    na, nb = np.isnan(a), np.isnan(b)
    same_nan = bool((na == nb).all())
    m = ~(na | nb)
    return same_nan, (float(np.max(np.abs(a[m] - b[m]))) if m.any() else 0.0)


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(ANC, exist_ok=True)
    t_start = time.time()
    _log('START %s  RES=%s' % (TASK, J.RES))
    src_sha = {f: J.sha_file(os.path.join(J.CODE, f)) for f in SRC_FILES}
    e5a_files = ['summary.csv', '_delivery_stats.csv', 'check.csv', 'pool1_I11_screening.csv'] + ['pool2_%s.csv' % P.FNAME[c] for c in P.DELIV]
    e5a_sha = {f: J.sha_file(os.path.join(J.E5A_RES, f)) for f in e5a_files}
    checks = []

    def chk(cid, obj, metric, expected, got, diff, tol, ok, note='', gate=True):
        """gate=False：只记录（不一致记 DIFFERS、不计入 FAIL）；ok=None 记 INFO。"""
        status = 'INFO' if ok is None else ('PASS' if ok else ('FAIL' if gate else 'DIFFERS'))
        checks.append(dict(check_id=cid, object=obj, metric=metric, expected=expected, got=got, abs_diff=diff, tol=tol,
                           status=status, gate=gate, note=note))
        if status in ('FAIL', 'DIFFERS'):
            _log('  %s %s %s %s expected=%s got=%s diff=%s' % (status, cid, obj, metric, expected, got, diff))

    rows6, rows8, chk_rows = [], [], []
    pool1_parts = []; pool2_parts = {c: [] for c in P.DELIV}
    ledgers = []; prof = []
    for pname in P.SEGS:
        t0 = time.time()
        ctx = P.build_period(pname)
        t1 = time.time()
        masks = P.form_masks(ctx)
        w_pool, pr_pool6, bm2 = P.pool_bench(ctx, 6.0)
        pr_pool8 = C.compute_calendar_pnl(w_pool, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=8.0)
        ex_p = pr_pool6['port_daily'] - bm2 * pr_pool6['daily_position']
        ledgers.append(ledger_frame(pname, 'POOL0_DEV', pr_pool6, pr_pool8, bm2,
                                    ex_p - pr_pool6['daily_turnover'] * 6.0 / 1e4, ex_p - pr_pool8['daily_turnover'] * 8.0 / 1e4))
        pool1_parts.append(P.pool1_part(ctx))
        for cfg in P.DELIV:
            hold, w = P.weights_of(ctx, masks[cfg])
            pr6 = C.compute_calendar_pnl(w, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=6.0)
            r6, net2_6 = P.summary_row(pname, cfg, hold, w, pr6, bm2, 6.0)
            pr8 = C.compute_calendar_pnl(w, ctx['data'], ctx['clean'], hold_days=5, cost_bp_bilateral=8.0)
            r8, net2_8 = P.summary_row(pname, cfg, hold, w, pr8, bm2, 8.0)
            rows6.append(r6); rows8.append(r8)
            if (pname, cfg) in P.ANCHORS_E4:
                anc = P.ANCHORS_E4[(pname, cfg)]; d = abs(r6['net_ann'] - anc)
                chk_rows.append(dict(period=pname, cfg=cfg, got=round(r6['net_ann'], 4), anchor=anc, dabs=round(d, 4), ok=bool(d < 0.02)))
            obj = '%s|%s' % (pname, cfg)
            # ③ 成本恒等：与成本无关的量逐位相同
            for key in ('gross_excess_daily', 'port_daily', 'bench_daily', 'daily_position', 'daily_turnover'):
                sn, md = maxabs_nanaware(pr6[key].values, pr8[key].values)
                chk('A1-C1', obj, '%s 6bp≡8bp' % key, 0.0, md, md, 0.0, sn and md == 0.0)
            resid = (pr8['net_excess_daily'] - pr6['net_excess_daily'] + 2e-4 * pr8['daily_turnover'])
            sn, _ = maxabs_nanaware(pr8['net_excess_daily'].values, pr6['net_excess_daily'].values)
            md = float(np.nanmax(np.abs(resid.values))) if resid.notna().any() else 0.0
            chk('A1-C2', obj, 'daily net8−net6+2e−4·turnover', 0.0, md, md, TOL_DAILY, sn and md <= TOL_DAILY)
            L = len(pr8['daily_turnover']); nn = int(r8['n'])
            hd_nan = float(pr8['daily_turnover'][pr8['net_excess_daily'].isna()].sum())
            exact = r6['net_ann'] - 0.02 * r6['turn'] * L / nn; d = abs(r8['net_ann'] - exact)
            chk('A1-C3', obj, 'net8_ann vs net6_ann−0.02·turn·L/n（缺失日换手=0）', exact, r8['net_ann'], d, TOL_ANN_EXACT,
                d <= TOL_ANN_EXACT and hd_nan == 0.0, 'L=%d n=%d 缺失日换手和=%s' % (L, nn, hd_nan))
            approx = r6['net_ann'] - 0.02 * r6['turn']
            chk('A1-C3a', obj, 'brief 近似式残差 net8_ann−(net6_ann−0.02·turn)', approx, r8['net_ann'], r8['net_ann'] - approx, '', None,
                '定义差：turn 按 L 行年化、净值按 n 个非缺失日年化；残差 = −0.02·turn·(L/n−1)', gate=False)
            if cfg == 'A4b_CVRv5':
                d = abs(r8['net_ann'] - W02_NET8_A4B_CVR[pname])
                chk('A1-C4', obj, 'net8_ann vs brief W02 换算值（两位小数、近似式）', W02_NET8_A4B_CVR[pname], r8['net_ann'], d, TOL_W02,
                    d <= TOL_W02, 'brief W02 由近似式换算；差异登记 source_resolution', gate=False)
            ledgers.append(ledger_frame(pname, cfg, pr6, pr8, bm2, net2_6, net2_8))
            pool2_parts[cfg].append(P.pool2_part(ctx, w))
        t2 = time.time()
        rss_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
        prof.append(dict(period=pname, load_s=round(t1 - t0, 1), forms_s=round(t2 - t1, 1), maxrss_gb=round(rss_gb, 2),
                         n_dates=len(ctx['pool0'].index), n_stocks=len(ctx['pool0'].columns)))
        _log('period %s done: load %.0fs, forms+pnl %.0fs, maxrss %.1f GB' % (pname, t1 - t0, t2 - t1, rss_gb))
        del ctx, masks, w_pool, pr_pool6, pr_pool8

    # ① pool2 六文件逐字节
    stats = []
    for cfg in P.DELIV:
        fn = 'pool2_%s.csv' % P.FNAME[cfg]
        b, dfp = P.pool2_bytes(pool2_parts[cfg])
        sha_new = J.sha_bytes(b); ok = (sha_new == e5a_sha[fn])
        nd = dfp.tradeDate.nunique()
        stats.append(dict(cfg=cfg, file=fn, rows=len(dfp), days=nd, avg_names=round(len(dfp) / nd, 1),
                          avg_wsum=round(dfp.weight.sum() / nd, 4), wmax=float(dfp.weight.max()), dmin=dfp.tradeDate.min(), dmax=dfp.tradeDate.max()))
        chk('A1-P1', fn, 'sha256 bytes', e5a_sha[fn], sha_new, '', '', ok, 'rows=%d days=%d %s..%s wmax=%s' % (
            len(dfp), nd, dfp.tradeDate.min(), dfp.tradeDate.max(), dfp.weight.max()))
        if not ok:   # 仅不一致时落盘复现件并做逐行差
            J.atomic_write_bytes(os.path.join(OUT, 'repro_' + fn), b)
            ref = pd.read_csv(os.path.join(J.E5A_RES, fn))
            m = ref.merge(dfp, on=['ticker', 'tradeDate'], how='outer', suffixes=('_e5a', '_repro'), indicator=True)
            both = m[m['_merge'] == 'both']
            chk('A1-P1d', fn, 'row diff', 0, int((m['_merge'] != 'both').sum()), '', 0, False,
                'only_e5a=%d only_repro=%d max|dw|=%.3g' % ((m['_merge'] == 'left_only').sum(), (m['_merge'] == 'right_only').sum(),
                                                          float(np.abs(both.weight_e5a - both.weight_repro).max()) if len(both) else 0.0))
    # pool1
    b1, p1 = P.pool1_bytes(pool1_parts)
    md5_new = hashlib.md5(b1).hexdigest()
    chk('A1-P0', 'pool1_I11_screening.csv', 'sha256 bytes', e5a_sha['pool1_I11_screening.csv'], J.sha_bytes(b1), '', '',
        J.sha_bytes(b1) == e5a_sha['pool1_I11_screening.csv'], 'md5=%s (源 POOL1_MD5 %s) rows=%d' % (md5_new, P.POOL1_MD5, len(p1)))
    # ② summary / _delivery_stats / check 逐字节 + summary 逐列数值
    s6 = pd.DataFrame(rows6)
    for fn, df in (('summary.csv', s6), ('_delivery_stats.csv', pd.DataFrame(stats)), ('check.csv', pd.DataFrame(chk_rows))):
        b = df.to_csv(index=False).encode('utf-8'); sha_new = J.sha_bytes(b)
        chk('A1-S1', fn, 'sha256 bytes', e5a_sha[fn], sha_new, '', '', sha_new == e5a_sha[fn])
        if sha_new != e5a_sha[fn]:
            J.atomic_write_bytes(os.path.join(OUT, 'repro_' + fn), b)
    ref = pd.read_csv(os.path.join(J.E5A_RES, 'summary.csv'), float_precision='round_trip')
    same_keys = list(ref[['period', 'cfg']].itertuples(index=False)) == list(s6[['period', 'cfg']].itertuples(index=False))
    chk('A1-S2', 'summary.csv', 'row keys (period,cfg) order', 24, len(s6), '', '', same_keys and len(s6) == 24)
    if same_keys:
        for col in ref.columns[2:]:
            d = float(np.nanmax(np.abs(ref[col].values.astype(float) - s6[col].values.astype(float))))
            chk('A1-S3', 'summary.csv', 'col %s max|Δ|' % col, 0.0, d, d, 0.0, d == 0.0)

    # ④ 母体账本与 6 / 8bp summary（已存在则逐位比对、不覆盖）
    led = pd.concat(ledgers, ignore_index=True)
    led_path = os.path.join(ANC, 'mother_ledger_prod_v2.parquet')
    if os.path.exists(led_path):
        old = pd.read_parquet(led_path)
        same = list(old.columns) == list(led.columns) and len(old) == len(led)
        if same:
            for col in led.columns:
                a, b = old[col].values, led[col].values
                same &= bool(np.array_equal(a.astype(float), b.astype(float), equal_nan=True)) if led[col].dtype.kind == 'f' \
                    else bool((a.astype(str) == b.astype(str)).all())
        chk('A1-L1', os.path.relpath(led_path, J.RES), 'existing ledger ≡ recomputed（逐列逐位，NaN 位置一致）', True, same, '', '', same)
    else:
        tmp = led_path + '.tmp.%d' % os.getpid(); led.to_parquet(tmp, index=False); os.replace(tmp, led_path)
    s6_path = os.path.join(ANC, 'mother_summary_6bp.csv'); s8_path = os.path.join(ANC, 'mother_summary_8bp.csv')
    for pth, df in ((s6_path, s6), (s8_path, pd.DataFrame(rows8))):
        b = df.to_csv(index=False).encode('utf-8')
        if os.path.exists(pth):
            chk('A1-L2', os.path.relpath(pth, J.RES), 'existing bytes ≡ recomputed', J.sha_file(pth), J.sha_bytes(b), '', '',
                J.sha_file(pth) == J.sha_bytes(b))
        else:
            J.atomic_write_bytes(pth, b)
    prof_path = os.path.join(OUT, 'profile.csv'); J.atomic_write_csv(prof_path, pd.DataFrame(prof))
    res = pd.DataFrame(checks)
    res_path = os.path.join(OUT, 'anchor1_results.csv'); J.atomic_write_csv(res_path, res)
    n_fail = int((res.status == 'FAIL').sum())
    man = dict(task=TASK, version=J.VERSION, env=J.env_versions(), src_sha256=src_sha, e5a_sha256=e5a_sha,
               n_checks=len(res), n_fail=n_fail, status_counts=res.status.value_counts().to_dict(),
               wall_s=round(time.time() - t_start, 1), profile=prof,
               supersedes=('stage0_anchor1_prod_path（FAILED：30 项全为检查定义错——A1-S3 read_csv 快速浮点解析、A1-C3 近似式容差、'
                           'A1-C4 对 brief 两位小数设门；生产口径数字零改动）') if RERUN else None,
               ledger=dict(path=os.path.relpath(led_path, J.RES), rows=len(led), cfgs=sorted(led.cfg.unique().tolist())))
    man_path = os.path.join(OUT, 'anchor1_manifest.json'); J.atomic_write_json(man_path, man)
    outs = [res_path, man_path, prof_path, led_path, s6_path, s8_path]
    if n_fail == 0:
        J.write_receipt(TASK, outs, 'SUCCEEDED', n_checks=len(res))
        _log('ALL PASS: %d checks; wall %.0fs' % (len(res), time.time() - t_start))
    else:
        J.write_receipt(TASK, outs, 'FAILED', n_checks=len(res), n_fail=n_fail, blocker=True)
        _log('BLOCKER: %d / %d checks FAIL; wall %.0fs' % (n_fail, len(res), time.time() - t_start))
    return 0 if n_fail == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
