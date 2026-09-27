# -*- coding: utf-8 -*-
"""E6j Stage 0 锚 3（brief v1.2 §2 第 3 项；plan §4.1 / §4.1a / §4.2）：SLOT 三规则恒等锚 + 无经济新增反例 + SRC vs E6i SLOT。
只算掩码 / 分数，不算任何收益（Stage 0 仪器；P / B 登记前不读新收益）。逐段一个进程（--segment），--merge 汇总。
  T1 α = 0：显式短路 ≡ 母体；α = 0 不短路（以 ptvol 作替身新分量）的混合 q ≡ q0、六形态掩码 ≡ 母体。
  T2 MA1 ≡ K0：e6f build_raw(K,1,MA,1e−4) 原值 = features_daily conditional_turnover（pool0 格逐位）；其生产坐标 pct = pcond；
     FALLBACK α ∈ {.25, 1} 六形态掩码 ≡ 母体。
  T3 FALLBACK α = 1 ≠ REPLACE（推导段，S 成员）：新有效格 q = q_new、缺失格 q = q0（结构恒等）；回退格数与两算子掩码差（INFO）。
  T4 反例 i：复制旧残差作 NEW → pct ≡ pcond；α ∈ {.125, .25, .5, 1} 六形态掩码 ≡ 母体。
  T5 反例 ii：复制旧残差、稳定哈希置 5% 格缺失、不重估 → SRC 秩坐标因有效 N 变小而移动 = rank_support_effect（INFO：掩码差格数）；
     TRANSPORT 同输入逐值回到 q0（PASS）、其 α .25 六形态掩码 ≡ 母体。
  T6 SRC vs E6i（推导段，R1 ≡ A4b_CVRv5 已证 exact_alias）：S / M / C1 × α{.125,.25,.5} 生产 SLOT 的 A4b_CVRv5 掩码 vs
     e6i_ops.Mother('R1').slot('K', …, 'FALLBACK')；成员生产坐标 pct vs E6i 已存 NS 表（特征合同）。
  T7 P 块全部成员（五臂 + 列对象）E6i 原值缓存 sha / 形状 / 特征截止日（四段；只读原值、不排名）。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob
import time
import resource

import numpy as np
import pandas as pd

import e6j_core as J
import e6j_prod as P
import e6j_slot as SL

TASK = 'stage0_anchor3_slot_identity'
OUT = os.path.join(J.RES, 'stage0', 'anchor3')
ARM_MEMBERS = {'S': ('K_rar20', 'lo', 'low_bad'), 'M': ('K_slope20', 'lo', 'low_bad'), 'C1': ('K_MA3_E6F', 'hi', 'high_bad')}
P_MEMBERS = ['K_rar20', 'K_slope20', 'K_MA3_E6F', 'K_rarpre', 'K_samt20', 'K_amt5', 'K_samt5', 'K_amt20']
ALPHAS = (0.125, 0.25, 0.5)
MISS_FRAC = 0.05


def mdiff(m1, m2):
    return {cfg: int((np.asarray(m1[cfg], bool) != np.asarray(m2[cfg], bool)).sum()) for cfg in P.DELIV}


def run_segment(pname):
    t0 = time.time()
    log = os.path.join(J.RES, 'logs', '%s_%s.log' % (TASK, pname))
    rows = []

    def chk(test, obj, metric, got, ok, note='', gate=True):
        status = 'INFO' if ok is None else ('PASS' if ok else ('FAIL' if gate else 'DIFFERS'))
        rows.append(dict(segment=pname, test=test, object=obj, metric=metric, got=got, status=status, gate=gate, note=note))
        if status in ('FAIL', 'DIFFERS'):
            J.log('  %s %s %s %s %s got=%s %s' % (status, pname, test, obj, metric, got, note), log)

    def chk_masks(test, lab, m, ref, gate=True, info=False):
        d = mdiff(m, ref)
        for cfg, n in d.items():
            chk(test, cfg, '%s 掩码差格数' % lab, n, None if info else (n == 0), gate=gate)
        return d

    ctx = P.build_period(pname)
    cc = SL.ccols_of(ctx)
    mother = P.form_masks(ctx)
    q0 = ctx['pcond']
    deriv = pname in J.DERIV_SEGS
    J.log('segment %s context ready %.0fs' % (pname, time.time() - t0), log)

    # ---- T1 α = 0
    chk_masks('T1', 'α=0 短路', SL.arm_masks(ctx, 'S', 0.0, members=None), mother)
    qz = SL.blend_q(q0, [(1.0, ctx['ptvol'])], 0.0)
    bitq = all(np.array_equal(qz[d].to_numpy(), q0[d].to_numpy()) and list(qz[d].index) == list(q0[d].index) for d in q0)
    chk('T1', 'q', 'α=0 不短路 q ≡ q0（逐位）', bitq, bitq)
    chk_masks('T1', 'α=0 不短路', P.form_masks(ctx, kq=qz), mother)

    # ---- T2 MA1 ≡ K0
    import e6f_core as F
    raw_ma1 = F.build_raw(ctx['data'], F.spec('K', 1, 'MA', 1e-4)).reindex(index=ctx['pool0'].index, columns=ctx['pool0'].columns)
    raw_k0 = ctx['specs'][P.F_COND]['func'](ctx['data'], ctx['feats'], ctx['industry']).reindex(
        index=ctx['pool0'].index, columns=ctx['pool0'].columns)
    a1, b1 = raw_ma1.values[ctx['p0']], raw_k0.values[ctx['p0']].astype(float)
    same_nan = bool((np.isnan(a1) == np.isnan(b1)).all())
    nd = int((a1[~np.isnan(a1)] != b1[~np.isnan(b1)]).sum()) if same_nan else -1
    chk('T2', 'K_MA1 vs K0', 'pool0 格原值不等格数（NaN 位置须一致）', nd, same_nan and nd == 0, 'cells=%d' % len(a1))
    p_ma1 = SL.pct_dir(SL.neu_of(ctx, raw_ma1), 'hi')
    dq = SL.dense(ctx, p_ma1); dq0 = SL.dense(ctx, q0)
    eq = bool(np.array_equal(dq, dq0, equal_nan=True))
    chk('T2', 'pct(MA1) vs pcond', '生产坐标 pct 逐位', eq, eq)
    for a in (0.25, 1.0):
        chk_masks('T2', 'MA1 FALLBACK α=%s' % a, P.form_masks(ctx, kq=SL.blend_q(q0, [(1.0, p_ma1)], a)), mother)
    del raw_ma1, raw_k0, p_ma1

    # ---- T4 反例 i：复制旧残差
    p_copy = SL.pct_dir({d: s.copy() for d, s in ctx['neu_cond'].items()}, 'hi')
    eq = all(np.array_equal(p_copy[d].to_numpy(), q0[d].to_numpy()) for d in q0)
    chk('T4', 'copy-old', 'pct(复制残差) ≡ pcond 逐位', eq, eq)
    for a in ALPHAS + (1.0,):
        chk_masks('T4', 'copy-old α=%s' % a, P.form_masks(ctx, kq=SL.blend_q(q0, [(1.0, p_copy)], a)), mother)

    # ---- T5 反例 ii：置缺失不重估 → rank_support_effect；TRANSPORT 恒等
    rng = J.rng_for('E6j', 'stage0', 'anchor3', 'T5_missing', pname)
    neu_miss, n_drop, n_all = {}, 0, 0
    for d in sorted(ctx['neu_cond']):
        s = ctx['neu_cond'][d]
        u = rng.random(len(s))
        keep = u >= MISS_FRAC
        n_drop += int((~keep).sum()); n_all += len(s)
        neu_miss[d] = s[keep].copy()
    p_miss = SL.pct_dir(neu_miss, 'hi')
    rse = chk_masks('T5', 'rank_support_effect α=.25（SRC 秩坐标）', P.form_masks(ctx, kq=SL.blend_q(q0, [(1.0, p_miss)], 0.25)),
                    mother, info=True)
    q_tr = SL.transport(q0, neu_miss, 'hi')
    eq = all(np.array_equal(q_tr[d].to_numpy(), q0[d].to_numpy()) for d in q0)
    chk('T5', 'TRANSPORT', '复制输入（5% 置缺失）TRANSPORT ≡ q0 逐位', eq, eq, 'dropped=%d/%d' % (n_drop, n_all))
    chk_masks('T5', 'TRANSPORT α=.25', P.form_masks(ctx, kq=SL.blend_q(q0, [(1.0, q_tr)], 0.25)), mother)
    del p_copy, neu_miss, p_miss, q_tr

    # ---- T7 成员原值缓存（四段；只读原值）
    for mid in P_MEMBERS:
        try:
            arr, meta = SL.e6i_member_raw(pname, mid)
            ok = arr.shape == (ctx['pool0'].shape[0], len(cc)) and meta['segment'] == pname
            chk('T7', mid, 'E6i 原值缓存 sha / 形状 / 截止日', '%s %s max_feature_date=%s warm=%s' % (
                meta['sha256'][:12], tuple(arr.shape), meta['max_feature_date'], meta['warm_tag']), ok)
        except Exception as e:   # noqa: BLE001
            chk('T7', mid, 'E6i 原值缓存', repr(e)[:200], False)

    ods = []
    if deriv:
        # ---- 成员生产坐标 pct 与 E6i 已存 NS 表（特征合同）
        members = {}
        for arm, (mid, dirc, _) in ARM_MEMBERS.items():
            pc, neu, meta = SL.member_pct(ctx, mid, dirc)
            members[arm] = pc
            e6 = SL.e6i_member_pct_table(pname, mid, dirc)
            eq = bool(np.array_equal(SL.dense(ctx, pc), e6, equal_nan=True))
            chk('T6', '%s:%s:%s' % (arm, mid, dirc), '生产坐标 pct vs E6i NS%s 表 逐位' % dirc, eq, eq)
            if arm == 'S':
                neu_S = neu
        # ---- T3 FALLBACK α = 1 ≠ REPLACE（S）
        q_fb = SL.blend_q(q0, [(1.0, members['S'])], 1.0)
        n_fb = n_new = 0; struct_ok = True
        for d, s0 in q0.items():
            sn = members['S'].get(d)
            sn = pd.Series(np.nan, index=s0.index) if sn is None else sn.reindex(s0.index)
            miss = sn.isna().to_numpy()
            n_fb += int(miss.sum()); n_new += int((~miss).sum())
            struct_ok &= bool(np.array_equal(q_fb[d].to_numpy()[miss], s0.to_numpy()[miss]))
            struct_ok &= bool(np.array_equal(q_fb[d].to_numpy()[~miss], sn.to_numpy()[~miss]))
        chk('T3', 'FALLBACK α=1', '缺失格 = q0、有效格 = q_new（结构）', struct_ok, struct_ok,
            '回退格 %d / 新有效格 %d' % (n_fb, n_new))
        chk_masks('T3', 'FALLBACK α=1 vs REPLACE α=1', P.form_masks(ctx, kq=q_fb),
                  P.form_masks(ctx, kq=SL.replace_q(members['S'], q0)), info=True)
        del q_fb, neu_S
        # ---- T6 SRC vs E6i SLOT（R1 ≡ A4b_CVRv5）
        import e6i_core as I
        import e6i_ops as O
        S6 = I.seg_i(pname, warm=False)
        if list(S6.pool0.columns[S6.ccols]) != list(ctx['pool0'].columns[cc]):
            chk('T6', 'grid', 'E6i ccols = 生产 ccols', False, False)
        else:
            M6 = O.Mother(S6, 'R1')
            for arm, (mid, dirc, role_dir) in ARM_MEMBERS.items():
                for a in ALPHAS:
                    b6, _ = M6.slot('K', (lambda mid=mid, role_dir=role_dir: O._dirpct(S6, mid, role_dir)), a, 'FALLBACK')
                    bp = SL.arm_masks(ctx, arm, a, members)['A4b_CVRv5'][:, cc]
                    n = int((np.asarray(b6, bool) != np.asarray(bp, bool)).sum())
                    chk('T6', 'A4b_CVRv5~R1 %s α=%s' % (arm, a), '生产 SLOT vs E6i Mother.slot 掩码差格数', n, n == 0,
                        'cells=%d' % int(np.asarray(b6, bool).sum()), gate=False)
                    ods.append(dict(segment=pname, form='A4b_CVRv5', src='E6i e6i_ops.Mother(R1).slot K FALLBACK', arm=arm,
                                    member=mid, direction=role_dir, alpha=a, mask_cells_differ=n,
                                    verdict='identical' if n == 0 else 'operator_discrepancy'))
            del S6, M6
    res = pd.DataFrame(rows)
    os.makedirs(OUT, exist_ok=True)
    J.atomic_write_csv(os.path.join(OUT, 'part_%s.csv' % pname), res)
    if ods:
        J.atomic_write_csv(os.path.join(OUT, 'ods_%s.csv' % pname), pd.DataFrame(ods))
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 / 1024.0
    J.atomic_write_json(os.path.join(OUT, 'part_%s.json' % pname), dict(segment=pname, wall_s=round(time.time() - t0, 1),
                                                                         maxrss_gb=round(rss, 2), n=len(res),
                                                                         n_fail=int((res.status == 'FAIL').sum())))
    J.log('segment %s done %.0fs maxrss %.1f GB; FAIL=%d' % (pname, time.time() - t0, rss, int((res.status == 'FAIL').sum())), log)
    return 0


def merge():
    parts = sorted(glob.glob(os.path.join(OUT, 'part_*.csv')))
    res = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    ods_parts = sorted(glob.glob(os.path.join(OUT, 'ods_*.csv')))
    ods = pd.concat([pd.read_csv(p) for p in ods_parts], ignore_index=True) if ods_parts else pd.DataFrame()
    segs = sorted(res.segment.unique())
    n_fail = int((res.status == 'FAIL').sum())
    res_path = os.path.join(OUT, 'anchor3_results.csv'); J.atomic_write_csv(res_path, res)
    ods_rows = ods.to_dict('records')
    for form in P.DELIV:
        if form != 'A4b_CVRv5':
            ods_rows.append(dict(segment='ALL', form=form, src='生产路径（无先行源 SLOT 实现）', arm='S/M/SM/C1', member='', direction='',
                                 alpha='', mask_cells_differ='', verdict='SPEC_only：本轮生产 SLOT 即 SRC；恒等锚 T1/T2/T4/T5'))
    ods_path = os.path.join(J.RES, 'operator_discrepancy_manifest.csv'); J.atomic_write_csv(ods_path, pd.DataFrame(ods_rows))
    rse = res[(res.test == 'T5') & res.metric.str.startswith('rank_support_effect')][['segment', 'object', 'got']]
    rse_path = os.path.join(OUT, 'rank_support_effect.csv'); J.atomic_write_csv(rse_path, rse)
    man = dict(task=TASK, version=J.VERSION, env=J.env_versions(), segments=segs, n_checks=len(res), n_fail=n_fail,
               status_counts=res.status.value_counts().to_dict(),
               src_sha256={f: J.sha_file(os.path.join(J.CODE, f)) for f in
                           ('e6j_boot.py', 'e6j_core.py', 'e6j_prod.py', 'e6j_slot.py', 'e6j_stage0_slot_identity.py', 'e6f_core.py',
                            'e6i_ops.py', 'e6i_core.py', 'e6i_s1base.py', 'e6g_core.py')},
               parts={os.path.basename(p): J.sha_file(p) for p in parts})
    man_path = os.path.join(OUT, 'anchor3_manifest.json'); J.atomic_write_json(man_path, man)
    ok = n_fail == 0 and len(segs) == 4
    J.write_receipt(TASK, [res_path, ods_path, rse_path, man_path], 'SUCCEEDED' if ok else 'FAILED', n_checks=len(res),
                    n_fail=n_fail, segments=segs, blocker=not ok)
    print('merge: %d checks, %d FAIL, segments=%s' % (len(res), n_fail, segs), flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    if '--merge' in sys.argv:
        sys.exit(merge())
    sys.exit(run_segment(sys.argv[sys.argv.index('--segment') + 1]))
