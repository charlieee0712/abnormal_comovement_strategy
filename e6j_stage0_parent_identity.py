# -*- coding: utf-8 -*-
"""E6j Stage 0 锚 2（brief v1.2 §2 第 2 项、W03；plan §3.2）：R1 vs A4b_CVRv5 四层身份 + R2 / A06 / A08 源锚。
生产侧 = e6j_prod（锚 1 已证逐位 = E5a）；研究侧 = E6i 同款段与母体（`e6i_core.seg_i(warm=False)` → `e6i_ops.Mother`
→ `e6i_engine.dev_weights / pnl_W`，只 import、不改）。逐段比较：
  L0 网格：pool0 / clean / 日期 / 列；
  L1 掩码：第一关（K 剔高半）、第二关（幸存集内 T 重中性化剔高半）、CVR_20d k5 否决、终掩码 —— 同源路径须逐格精确；
  L2 DEV 目标权重；L3 五日实际持仓；L4 8bp 日账本（gross / pos / turn / net）；
  L4b 研究侧重算 vs E6i 已存母体日账本（任一 H5 子账户的 net8 − dnet8）；R2 / A06 / A08 也做 L4b（源锚）；
  展示口径：E5a（avg_nh / avg_pos 只在有持仓日平均）与 E6i（parent_n_mean / pos_mean 全日平均）在同一掩码 / 账本上各算一遍。
浮点容差（plan §3.2，不抄 1e−15）：tol = 4 × n_terms × eps × scale（scale = 该层最大绝对值，n_terms = 当层最大求和项数）；
掩码只认精确。输出 stage0/anchor2/ + parent_identity_map.csv；任一 FAIL → 回执 FAILED（BLOCKER）。"""
import e6j_boot  # noqa: F401
import os
import sys
import time
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import comprehensive_factor_diagnosis as C
import e6i_core as I
import e6i_ops as O
import e6i_engine as E

RERUN = '--rerun' in sys.argv
TASK = 'stage0_anchor2_parent_identity' + ('_rerun' if RERUN else '')
OUT = os.path.join(J.RES, 'stage0', 'anchor2_rerun' if RERUN else 'anchor2')
LOG = os.path.join(J.RES, 'logs', TASK + '.log')
EPS = np.finfo(np.float64).eps
MOTHERS = ('R1', 'R2', 'A06', 'A08')
ROUTE_FOR = {'R1': 'RK', 'R2': 'RK', 'A06': 'RK', 'A08': 'RT'}
SRC_FILES = ['e6j_boot.py', 'e6j_core.py', 'e6j_prod.py', 'e6j_stage0_parent_identity.py', 'e6i_core.py', 'e6i_ops.py',
             'e6i_engine.py', 'e6h_run_routes.py', 'e6g_core.py', 'e6g_desc.py', 'e6f_core.py', 'e6e_core.py',
             'comprehensive_factor_diagnosis.py', 'export_delivery_pools_v2.py']


def _log(m):
    J.log(m, LOG)


def fcmp(a, b):
    """NaN 位置须一致；返回 (NaN 一致?, max|Δ|, scale, 逐位相同格占比)。"""
    a = np.asarray(a, float); b = np.asarray(b, float)
    na, nb = np.isnan(a), np.isnan(b)
    m = ~(na | nb)
    d = np.abs(a[m] - b[m]) if m.any() else np.zeros(1)
    scale = float(max(np.max(np.abs(a[m])) if m.any() else 0.0, np.max(np.abs(b[m])) if m.any() else 0.0))
    return bool((na == nb).all()), float(d.max()), scale, float((d == 0).mean())


def e6i_parent_ledger(pname, mn):
    """E6i 已存母体日账本：该母体任一 H5 子账户（ROUTE_FOR 路由）的 net8 − dnet8（两者均有限处）。"""
    base = os.path.join(J.E6I_RES, 'accounts', pname)
    idx = pd.read_csv(os.path.join(base, 'merged_index.csv'))
    sel = idx[(idx.route == ROUTE_FOR[mn]) & idx.descriptor_id.str.contains('|%s|' % mn, regex=False)
              & idx.descriptor_id.str.endswith('|H5')]
    if not len(sel):
        return None
    r = sel.iloc[0]
    z = np.load(os.path.join(base, r.npz), allow_pickle=False)
    row = int(r.row)
    if str(z['descriptor_id'][row]) != r.descriptor_id:
        raise RuntimeError('E6i npz 行与索引不符: %s' % r.descriptor_id)
    net8, dnet8 = z['net8'][row].astype(float), z['dnet8'][row].astype(float)
    csv = pd.read_csv(os.path.join(base, r.npz.replace('.npz', '.csv')))
    c = csv[csv.descriptor_id == r.descriptor_id].iloc[0]
    return dict(descriptor_id=r.descriptor_id, npz=r.npz, row=row, parent=np.where(np.isfinite(dnet8), net8 - dnet8, np.nan),
                parent_net8_ann=float(c.parent_net8_ann), parent_n_mean=float(c.parent_n_mean))


def main():
    os.makedirs(OUT, exist_ok=True)
    t_start = time.time()
    _log('START %s' % TASK)
    src_sha = {f: J.sha_file(os.path.join(J.CODE, f)) for f in SRC_FILES}
    led_all = pd.read_parquet(os.path.join(J.RES, 'anchors', 'mother_ledger_prod_v2.parquet'))
    checks, disp, l4b_rows, prof = [], [], [], []

    def chk(cid, seg, obj, metric, got, tol, ok, note='', gate=True, expected=''):
        status = 'INFO' if ok is None else ('PASS' if ok else ('FAIL' if gate else 'DIFFERS'))
        checks.append(dict(check_id=cid, segment=seg, object=obj, metric=metric, expected=expected, got=got, tol=tol,
                           status=status, gate=gate, note=note))
        if status in ('FAIL', 'DIFFERS'):
            _log('  %s %s %s %s %s got=%s tol=%s %s' % (status, cid, seg, obj, metric, got, tol, note))

    def cmp_layer(cid, seg, obj, metric, a, b, n_terms):
        sn, md, scale, fr = fcmp(a, b)
        tol = 4.0 * n_terms * EPS * max(scale, 1e-300)
        chk(cid, seg, obj, metric, md, tol, sn and md <= tol,
            'NaN 位置%s；scale=%.3g；逐位相同占比 %.6f；max|Δ|/(eps·scale)=%.1f' % (
                '一致' if sn else '不一致', scale, fr, md / (EPS * scale) if scale > 0 else 0.0))
        return md

    for pname in P.SEGS:
        t0 = time.time()
        ctx = P.build_period(pname)
        pool0 = ctx['pool0']; N = pool0.shape[1]
        masks = P.form_masks(ctx)
        hc = (C.build_factor_strategy_holdings_cached(ctx['neu_cond'], pool0, 2, [2]).values == 1)
        tox = P.drop_mask(ctx['neu_cvr'], pool0, 5)
        S = I.seg_i(pname, warm=False)
        cc = np.asarray(S.ccols)
        # ---- L0 网格
        same_grid = list(S.pool0.index) == list(pool0.index) and list(S.pool0.columns) == list(pool0.columns)
        chk('A2-L0', pname, 'grid', 'pool0 index/columns 相同', same_grid, '', same_grid)
        chk('A2-L0', pname, 'pool0', 'pool0 values 逐格', bool(same_grid and np.array_equal(S.pool0.values, pool0.values)), '',
            bool(same_grid and np.array_equal(S.pool0.values, pool0.values)))
        if hasattr(S, 'clean'):
            ok = bool(np.array_equal(np.asarray(S.clean.values, float), np.asarray(ctx['clean'].values, float)))
            chk('A2-L0', pname, 'clean', 'clean 基准池逐格', ok, '', ok)
        outside = np.setdiff1d(np.arange(N), cc)
        for cfg in P.DELIV:
            bad = int(masks[cfg][:, outside].sum()) if len(outside) else 0
            chk('A2-L0', pname, cfg, 'ccols 之外持仓格数', bad, 0, bad == 0)
        if not same_grid:
            _log('  grid differs in %s; skip deeper layers' % pname); continue
        # ---- L1 掩码（R1 vs A4b_CVRv5 分关）
        M = O.Mother(S, 'R1')
        keep_dep, _, _ = M._keep_dep()
        for lab, a, b in (('第一关 K 剔高半 (hc vs Mother.s1)', hc[:, cc], M.s1),
                          ('第二关 T 幸存集内 (A4b vs keep_dep)', masks['A4b'][:, cc], keep_dep),
                          ('CVR_20d k5 否决 (drop_mask vs veto_drop)', tox[:, cc], M.veto_drop()),
                          ('终掩码 (A4b_CVRv5 vs Mother.B)', masks['A4b_CVRv5'][:, cc], M.B)):
            nd = int((np.asarray(a, bool) != np.asarray(b, bool)).sum())
            chk('A2-L1', pname, 'R1~A4b_CVRv5', lab, nd, 0, nd == 0, 'cells=%d' % int(np.asarray(b, bool).sum()))
        # ---- L2 目标权重
        hold, Wp_full = P.weights_of(ctx, masks['A4b_CVRv5'])
        Wp = Wp_full.values[:, cc]
        Wr = E.dev_weights(S, M.B)
        nmax = int(M.B.sum(1).max())
        cmp_layer('A2-L2', pname, 'R1~A4b_CVRv5', 'DEV 目标权重', Wp, Wr, nmax)
        # ---- L3 五日实际持仓
        act_p = Wp_full.rolling(5, min_periods=1).mean().values[:, cc]
        act_r = E._act(Wr, 5)
        cmp_layer('A2-L3', pname, 'R1~A4b_CVRv5', '五日实际持仓 (rolling mean vs _act)', act_p, act_r, 5 * nmax)
        # ---- L4 8bp 日账本
        g, p, u, n = E.pnl_W(S, Wr, 5, 8.0)
        L = led_all[(led_all.period == pname) & (led_all.cfg == 'A4b_CVRv5')]
        same_dates = len(L) == S.T and list(L.date) == [pd.Timestamp(str(d)).strftime('%Y-%m-%d') for d in S.pool0.index]
        chk('A2-L4', pname, 'R1~A4b_CVRv5', '日账本日期轴相同（生产 vwap 索引 vs 研究 pool0 索引）', same_dates, '', same_dates)
        if not same_dates:
            continue
        for lab, a, b, nt in (('gross', L.gross_excess.values, g, len(cc)), ('pos', L.daily_position.values, p, 5 * nmax),
                              ('turn', L.daily_turnover.values, u, 10 * nmax), ('net8', L.net8.values, n, len(cc))):
            cmp_layer('A2-L4', pname, 'R1~A4b_CVRv5', '日账本 %s' % lab, a, b, nt)
        ann_p, ann_r = float(np.nanmean(L.net8.values)) * J.ANN, float(np.nanmean(n)) * J.ANN
        chk('A2-L4a', pname, 'R1~A4b_CVRv5', 'net8 年化（生产 vs 研究）', ann_r - ann_p, '', None,
            'prod=%.6f research=%.6f' % (ann_p, ann_r), gate=False)
        # ---- 展示口径（同一掩码 / 账本上两种定义）
        nh = masks['A4b_CVRv5'].sum(1); wsum = Wp_full.values.sum(1)
        disp.append(dict(segment=pname, object='A4b_CVRv5≡R1(本锚)',
                         E5a_avg_nh=float(nh[nh > 0].mean()), E6i_parent_n_mean=float(M.B.sum(1).mean()),
                         E5a_avg_pos=float(wsum[wsum > 0].mean()), E6i_pos_mean=float(np.nanmean(p)),
                         days=len(nh), days_nh_pos=int((nh > 0).sum()),
                         net8_ann_prod=ann_p, net8_ann_research=ann_r))
        # ---- L4b 研究侧重算 vs E6i 已存母体账本（R1 / R2 / A06 / A08）
        for mn in MOTHERS:
            Mm = M if mn == 'R1' else O.Mother(S, mn)
            Wm = Wr if mn == 'R1' else E.dev_weights(S, Mm.B)
            _, _, _, nm = E.pnl_W(S, Wm, 5, 8.0)
            st = e6i_parent_ledger(pname, mn)
            if st is None:
                chk('A2-L4b', pname, mn, 'E6i 已存母体账本', 'UNAVAILABLE', '', False, '无 H5 子账户'); continue
            both = np.isfinite(st['parent'])
            sn, md, scale, fr = fcmp(np.where(both, nm, np.nan), st['parent'])
            tol = 4.0 * len(cc) * EPS * max(scale, 1e-300)
            chk('A2-L4b', pname, mn, '研究重算 vs E6i 已存 net8 日账本（%s）' % st['descriptor_id'], md, tol, md <= tol,
                'finite days=%d / %d；逐位相同占比 %.6f' % (int(both.sum()), len(both), fr))
            ann_r_m = float(np.nanmean(nm)) * J.ANN
            chk('A2-L4c', pname, mn, 'net8 年化 vs E6i parent_net8_ann', abs(ann_r_m - st['parent_net8_ann']), 1e-9,
                abs(ann_r_m - st['parent_net8_ann']) <= 1e-9, 'recomputed=%.6f E6i=%.6f' % (ann_r_m, st['parent_net8_ann']))
            chk('A2-L4c', pname, mn, 'parent_n_mean vs E6i', abs(float(Mm.B.sum(1).mean()) - st['parent_n_mean']), 1e-9,
                abs(float(Mm.B.sum(1).mean()) - st['parent_n_mean']) <= 1e-9)
            l4b_rows.append(dict(segment=pname, mother=mn, descriptor_id=st['descriptor_id'], net8_ann_recomputed=ann_r_m,
                                 E6i_parent_net8_ann=st['parent_net8_ann'], parent_n_mean=float(Mm.B.sum(1).mean()),
                                 E6i_parent_n_mean=st['parent_n_mean'], max_abs_daily=md))
        t1 = time.time(); rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
        prof.append(dict(segment=pname, wall_s=round(t1 - t0, 1), maxrss_gb=round(rss, 2)))
        _log('segment %s done: %.0fs maxrss %.1f GB' % (pname, t1 - t0, rss))
        del ctx, masks, S, M

    res = pd.DataFrame(checks)
    n_fail = int((res.status == 'FAIL').sum())
    # parent_identity_map：R1 ↔ A4b_CVRv5 分类（plan §3.2 / brief §2 第 2 项）
    def layer_ok(cid):
        s = res[(res.check_id == cid)]
        return bool(len(s)) and bool((s.status == 'PASS').all())
    l1, l2, l3, l4 = layer_ok('A2-L1'), layer_ok('A2-L2'), layer_ok('A2-L3'), layer_ok('A2-L4')
    grid = layer_ok('A2-L0')
    if grid and l1 and l2 and l3 and l4:
        cls = 'exact_alias'
    elif grid and l1:
        cls = 'same_structure_diff_impl'
    else:
        cls = 'different'
    def layer_max(cid):
        """只取数值层（DEV / 持仓 / 日账本 各列的 max|Δ|）；排除布尔型的日期轴检查（首跑把 True 计成 1.0，见 supersedes）。"""
        s = res[(res.check_id == cid) & ~res.metric.str.contains('日期轴')]
        v = pd.to_numeric(s.got, errors='coerce')
        return float(v.max()) if v.notna().any() else float('nan')
    pim = pd.DataFrame([dict(
        object_a='R1 (E6i research: KT_dep(50,50)|C:k5)', object_b='A4b_CVRv5 (production v2)', classification=cls,
        alias_of=('A4b_CVRv5' if cls == 'exact_alias' else ''),
        L0_grid=grid, L1_mask_exact=l1, L2_weights_tol=l2, L3_holdings_tol=l3, L4_daily_tol=l4,
        L2_max_abs=layer_max('A2-L2'), L3_max_abs=layer_max('A2-L3'), L4_max_abs=layer_max('A2-L4'),
        diff_pool0=not grid, diff_neutralize_scope=not layer_ok_sub(res, '第二关'), diff_bin_ties=not layer_ok_sub(res, '第一关'),
        diff_dev=not l2, diff_cost=False,
        note='掩码逐格精确 + 权重 / 持仓 / 日账本在浮点求和序容差内 → exact_alias；历史暴露（S / M / C1 已在 R1 见过）不因别名抹除')])
    pim_path = os.path.join(J.RES, 'parent_identity_map.csv')
    if not RERUN or not os.path.exists(pim_path):
        J.atomic_write_csv(pim_path, pim)
    else:
        J.atomic_write_csv(os.path.join(OUT, 'parent_identity_map_rerun.csv'), pim)
    res_path = os.path.join(OUT, 'anchor2_results.csv'); J.atomic_write_csv(res_path, res)
    disp_path = os.path.join(OUT, 'display_metric_reconciliation.csv'); J.atomic_write_csv(disp_path, pd.DataFrame(disp))
    l4b_path = os.path.join(OUT, 'e6i_parent_anchor.csv'); J.atomic_write_csv(l4b_path, pd.DataFrame(l4b_rows))
    man = dict(task=TASK, version=J.VERSION, env=J.env_versions(), src_sha256=src_sha, n_checks=len(res), n_fail=n_fail,
               status_counts=res.status.value_counts().to_dict(), classification=cls, profile=prof,
               wall_s=round(time.time() - t_start, 1),
               supersedes=('stage0_anchor2_parent_identity（SUCCEEDED；根目录 parent_identity_map.csv 的 L4_max_abs = 1.0 是汇总伪值：'
                           'layer_max 把布尔日期轴检查 True 计成 1.0；真实 L4 max|Δ| 见本次 parent_identity_map_rerun.csv；'
                           '其余列与分类不变）') if RERUN else None)
    man_path = os.path.join(OUT, 'anchor2_manifest.json'); J.atomic_write_json(man_path, man)
    outs = [res_path, disp_path, l4b_path, man_path, pim_path]
    J.write_receipt(TASK, outs, 'SUCCEEDED' if n_fail == 0 else 'FAILED', n_checks=len(res), n_fail=n_fail,
                    classification=cls, blocker=(n_fail > 0))
    _log('%s: %d checks, %d FAIL, classification=%s; wall %.0fs' % ('ALL PASS' if n_fail == 0 else 'BLOCKER', len(res), n_fail, cls,
                                                                    time.time() - t_start))
    return 0 if n_fail == 0 else 2


def layer_ok_sub(res, key):
    s = res[(res.check_id == 'A2-L1') & res.metric.str.contains(key)]
    return bool(len(s)) and bool((s.status == 'PASS').all())


if __name__ == '__main__':
    sys.exit(main())
