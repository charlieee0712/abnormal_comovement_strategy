# -*- coding: utf-8 -*-
"""E6m 阶段 S 补充件 S1（2026-10-12，用户定"现在补算成补充件"；补丁十九）。
对象：附属 item 6 · SAME_N_CORE_DEEP（aux_kind V_SAME_N_CORE_DEEP）× 补充 owner（SUPP:，V_ALL_KNOWN 诊断）共 240 行（H1–H20 各 12）。
主路径漏算：e6m_s_aux.main 按形态筛 owner 只认带 '|' 的编号，SUPP: 编号全被跳过，SAME_N_CORE_DEEP 的 SUPP 分支成死代码（补丁十九已修，只影响以后的重跑）。
做法（不改任何封存件；只读 masks/<段>/ 与登记）：
  名单  e6m_s_aux.Aux.v_same_n_core_deep，cfg 与主路径 SUPP 分支同式（operator / param 取 supplemental，condition = ALL_KNOWN）
        → supp/S1/masks_aux/<段>/<形态>.npz（与 masks_aux 同格式）+ facts_aux_<形态>.csv
  账户  e6m_s_accounts.run_aux（only_keys = 本补充键，skip_fpwd = True）→ supp/S1/accounts_aux/<段>/<形态>.npz + facts_aux_accounts_<形态>.csv
  回执  S_supp1_<段>_<形态>；manifest → supp/S1/supp_S1_manifest.json + supp_S1_summary.csv
用法：python e6m_s_supp1.py run --seg <段> [--forms a,b]
      python e6m_s_supp1.py manifest
      python e6m_s_supp1.py verify --seg <段> --form <形态> --n 4 --out <沙箱目录>
verify：取 n 个常规 V 的 SAME_N_CORE_DEEP 行走同一条路（cfg 与主路径常规分支同式），与封存件 masks_aux / accounts_aux 逐位比对；只写沙箱。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import glob
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M

MECH = 'SAME_N_CORE_DEEP'


def sroot(*a):
    return M.P('supp', 'S1', *a)


def manifest_rows():
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    SUP = M.read_csv_keep(M.P('registry', 'supplemental_E6m.csv'), dtype=str)
    return A, SUP


def supp_targets(A, SUP):
    X = A[(A['item'] == '6') & (A.mechanism == MECH) & A.owner_id.str.startswith('SUPP:')].copy()
    X['own'] = X.owner_id.str.split('@').str[0]
    X['form'] = X.own.map(lambda o: SUP[SUP.supp_id.str.startswith(o[5:])].parent.iloc[0])
    return X


def cfg_supp(own, SUP):
    s = SUP[SUP.supp_id.str.startswith(own[5:])].iloc[0]                       # 同 e6m_s_aux.main 的 SUPP 分支
    return dict(operator=s.operator, param=s.param, condition='ALL_KNOWN')


def cfg_regular(own, SUP):
    import e6m_s_aux as AX
    o = AX.parse_desc(own)                                                      # 同 e6m_s_aux.main 的常规分支
    return dict(operator=o['operator'], param=str(o['param']), condition=o['condition'])


def build_lists(seg_name, form, rows, cfg_of, SUP):
    import e6m_s_run_masks as RM
    import e6m_s_aux as AX
    R = RM.Runner(seg_name, form, 'real')
    A = AX.Aux(R)
    memo, ids, finals, facts = {}, [], [], []
    for r in rows.itertuples():
        cfg = cfg_of(r.own, SUP)
        sig = tuple(sorted(cfg.items()))
        if sig not in memo:
            memo[sig] = A.v_same_n_core_deep(cfg)
        F, f = memo[sig]
        key = '%s|%s' % (r.aux_id, MECH)
        ids.append(key)
        finals.append(np.packbits(F))
        facts.append(dict(aux_key=key, kind=MECH, status='COMPUTED', final_members=int(F.sum()), final_vs_parent=int((F != R.F0).sum()),
                          **{('f_' + k): v for k, v in (f or {}).items()}))
    return R, ids, finals, facts, len(memo)


def write_lists(od, form, R, ids, finals, facts):
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'facts_aux_%s.csv' % form)
    p2 = os.path.join(od, '%s.npz' % form)
    M.atomic_write_csv(p1, pd.DataFrame(facts))
    M.atomic_write_npz(p2, aux_keys=np.array(ids), final_bits=np.array(finals), n_cells=np.array([R.seg.n]), status=np.array(['ANCHOR_PENDING']))
    return p1, p2


def task_run(seg_name, forms=None):
    import e6m_s_real as RL
    import e6m_s_gate as GT
    import e6m_s_accounts as ACC
    import e6m_s_aux as AX
    GT.post_gate(seg_name, 'supp1 %s' % seg_name)
    A, SUP = manifest_rows()
    X = supp_targets(A, SUP)
    fl = sorted(X.form.unique()) if not forms else forms
    seg = None
    rc = 0
    for form in fl:
        t0 = time.time()
        rows = X[X.form == form]
        if not len(rows):
            continue
        R, ids, finals, facts, n_lists = build_lists(seg_name, form, rows, cfg_supp, SUP)
        p1, p2 = write_lists(sroot('masks_aux', seg_name), form, R, ids, finals, facts)
        del R
        if seg is None:
            seg = RL.seg_of(seg_name, 'real')
        pa, pf = ACC.run_aux(seg, form, M.P('masks', seg_name), sroot('masks_aux', seg_name), sroot('accounts_aux', seg_name),
                             only_keys=set(ids), skip_fpwd=True)
        Fa = M.read_csv_keep(pf, dtype=str)
        ok = bool((len(Fa) == len(ids)) and set(Fa.aux_key) == set(ids) and (Fa.status == 'COMPUTED').all())   # 补丁二十：numpy bool → bool
        rc |= 0 if ok else 1
        T = dict(rows=len(ids), distinct_lists=n_lists, accounts_computed=int((Fa.status == 'COMPUTED').sum()), wall_s=round(time.time() - t0, 1),
                 rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
        M.write_receipt('S_supp1_%s_%s' % (seg_name, form), [p1, p2, pa, pf], status='SUCCEEDED' if ok else 'FAILED',
                        code=[__file__, AX.__file__, ACC.__file__, M.__file__], note='补充件 S1：item 6 SAME_N_CORE_DEEP × SUPP V_ALL_KNOWN（不读收益；不改封存件）', **T)
        print(json.dumps(dict(seg=seg_name, form=form, ok=ok, **T), ensure_ascii=False, default=str), flush=True)
    return rc


def task_manifest():
    A, SUP = manifest_rows()
    X = supp_targets(A, SUP)
    rows, files = [], {}
    for s in M.SEGMENTS:
        for form in sorted(X.form.unique()):
            want = set('%s|%s' % (a, MECH) for a in X[X.form == form].aux_id)
            fm, fa = sroot('masks_aux', s, 'facts_aux_%s.csv' % form), sroot('accounts_aux', s, 'facts_aux_accounts_%s.csv' % form)
            Fm = M.read_csv_keep(fm, dtype=str) if os.path.exists(fm) else pd.DataFrame(columns=['aux_key', 'status'])
            Fa = M.read_csv_keep(fa, dtype=str) if os.path.exists(fa) else pd.DataFrame(columns=['aux_key', 'status'])
            pr = M.P('task_status', 'S_supp1_%s_%s.receipt.json' % (s, form))
            rc = json.load(open(pr, encoding='utf-8')).get('status', 'MISSING') if os.path.exists(pr) else 'MISSING'
            rows.append(dict(segment=s, form=form, target_rows=len(want), list_rows=int(Fm.aux_key.isin(want).sum()),
                             account_rows_computed=int((Fa.aux_key.isin(want) & (Fa.status == 'COMPUTED')).sum()), receipt=rc,
                             status='COMPUTED' if (int((Fa.aux_key.isin(want) & (Fa.status == 'COMPUTED')).sum()) == len(want) and rc == 'SUCCEEDED') else 'NOT_RUN'))
    for p in sorted(glob.glob(sroot('**', '*'), recursive=True)):
        if os.path.isfile(p) and not p.endswith(('supp_S1_manifest.json', 'supp_S1_summary.csv')):
            files[M.rel(p)] = M.sha_file(p)
    S = pd.DataFrame(rows)
    ps = sroot('supp_S1_summary.csv')
    M.atomic_write_csv(ps, S)
    man = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, supplement='S1', basis='用户 2026-10-12 原话"现在补算成补充件"（S10 覆盖：240 行未算）',
               object='附属 item 6 · SAME_N_CORE_DEEP × SUPP V_ALL_KNOWN', target_rows=int(len(X)), segments=list(M.SEGMENTS), forms=sorted(X.form.unique()),
               sealed_untouched='封存件（masks / masks_aux / accounts / accounts_aux / stage_a / randoms）不改；只读 masks/<段>/',
               all_computed=bool((S.status == 'COMPUTED').all()), files=files, summary=M.rel(ps))
    M.atomic_write_json(sroot('supp_S1_manifest.json'), man)
    print(json.dumps(dict(all_computed=man['all_computed'], files=len(files), rows=int(S.target_rows.sum())), ensure_ascii=False), flush=True)
    return 0 if man['all_computed'] else 1


def task_verify(seg_name, form, n, out):
    """他算 / 基线：常规 V 行走补充件同一条路，与封存件逐位比对（只写沙箱 out）。"""
    import e6m_s_real as RL
    import e6m_s_accounts as ACC
    import e6m_s_gate as GT
    GT.post_gate(seg_name, 'supp1 verify %s' % seg_name)
    A, SUP = manifest_rows()
    X = A[(A['item'] == '6') & (A.mechanism == MECH) & ~A.owner_id.str.startswith('SUPP:')].copy()
    X['own'] = X.owner_id.str.split('@').str[0]
    X = X[X.own.map(lambda o: o.split('|')[1] == form)]
    zs = np.load(M.P('masks_aux', seg_name, '%s.npz' % form), allow_pickle=False)
    sealed_keys = {str(k): j for j, k in enumerate(zs['aux_keys'])}
    X = X[X.aux_id.map(lambda a: ('%s|%s' % (a, MECH)) in sealed_keys)]
    pick = X.drop_duplicates('own').head(n)
    pick = pd.concat([pick, X[X.own.isin(pick.own) & ~X.aux_id.isin(pick.aux_id)].head(n)])     # 同 owner 不同 H 也取几行（核 memo 复用）
    R, ids, finals, facts, n_lists = build_lists(seg_name, form, pick, cfg_regular, SUP)
    res = []
    for k, b in zip(ids, finals):
        res.append(('list %s' % k, bool(np.array_equal(b, zs['final_bits'][sealed_keys[k]]))))
    od_m, od_a = os.path.join(out, 'masks_aux'), os.path.join(out, 'accounts_aux')
    write_lists(od_m, form, R, ids, finals, facts)
    del R
    seg = RL.seg_of(seg_name, 'real')
    pa, pf = ACC.run_aux(seg, form, M.P('masks', seg_name), od_m, od_a, only_keys=set(ids), skip_fpwd=True)
    zn = np.load(pa, allow_pickle=False)
    zo = np.load(M.P('accounts_aux', seg_name, '%s.npz' % form), allow_pickle=False)
    import e6k_acct as AC
    tn = {str(k): j for j, k in enumerate(zn['targets'])}
    to = {str(k): j for j, k in enumerate(zo['targets'])}
    dn = {(str(d), int(h)): j for j, (d, h) in enumerate(zip(zn['desc'], zn['desc_H']))}
    do = {(str(d), int(h)): j for j, (d, h) in enumerate(zip(zo['desc'], zo['desc_H']))}
    for k in ids:
        res.append(('acct target bits %s' % k, bool(np.array_equal(zn['bits'][tn[k]], zo['bits'][to[k]]))))
        res.append(('acct target stats %s' % k, all(np.array_equal(zn['t_' + q][tn[k]], zo['t_' + q][to[k]], equal_nan=True) for q in AC.TGT_KEYS)))
    for key in dn:
        res.append(('acct ledger %s H%d' % key, all(np.array_equal(zn['d_' + q][dn[key]], zo['d_' + q][do[key]], equal_nan=True) for q in AC.DESC_KEYS)))
    bad = [r for r, ok in res if not ok]
    print(json.dumps(dict(seg=seg_name, form=form, rows=len(ids), distinct_lists=n_lists, checks=len(res), bad=bad[:5], verdict='PASS' if not bad else 'FAIL'),
                     ensure_ascii=False), flush=True)
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['run', 'manifest', 'verify'])
    ap.add_argument('--seg')
    ap.add_argument('--forms', default='')
    ap.add_argument('--form')
    ap.add_argument('--n', type=int, default=4)
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.task == 'run':
        return task_run(a.seg, [x for x in a.forms.split(',') if x] or None)
    if a.task == 'manifest':
        return task_manifest()
    return task_verify(a.seg, a.form, a.n, a.out)


if __name__ == '__main__':
    sys.exit(main())
