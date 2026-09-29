# -*- coding: utf-8 -*-
"""E6k 确定性账户（brief §5 A2；W10 存储合同；plan §5–§8）。一个任务 = (段, 母体, 测量)：该 (母体, 测量) 的全部登记描述符
（CORE / OWN / REPAIR / LAYER / BAND / BAND_COMPARATOR / TREFIT / POST2 / RAR / SM_ANCHOR；测量 K0 = PARENT / HG_ONLY）+ 附属
（INC 72、BAND 剂量控制、COMMON_SUPPORT 子 / 父）。目标（形成日名单 → DEV）与 H 无关：每个目标算一次，H 列表走稀疏账本。
登记门：registration/{P,B}_package_manifest_E6k.json 存在且 registry sha 一致；后段另过 e6k_core.post_gate（方式 A 未授权时拒绝）。
--profile：新测量换成当日内置换（固定种子；无真实新信息，只测时 / 测资源），写临时目录，不写回执、不登记。
输出：accounts/<段>/<母体>__<测量>.npz（描述符 × 日：DESC_KEYS；目标 × 日：TGT_KEYS；掩码位图）+ weights_<…>.npz（固定清单目标权重）
+ facts_<…>.csv（每目标机械事实：RP 求解 / 回退 / 剂量标志 / 插值不可用日 / 编辑数）；回执 task_status/run_det_<段>_<母体>__<测量>。"""
import e6k_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_env as E
import e6k_ops as O
import e6k_acct as AC
import e6j_engine as EN

LANDMARK = (3, 5, 10, 20)
TAUS = {'RP0p5': 0.5, 'RP1': 1.0, 'RP3': 3.0, 'RPINF': None}


def registration_ok(reg_dir):
    for nm in ('P_package_manifest_E6k.json', 'B_package_manifest_E6k.json'):
        p = K.P('registration', nm)
        if not os.path.exists(p):
            return False, '%s 未登记' % nm
        m = json.load(open(p, encoding='utf-8'))
        for f, s in m['registry_sha256'].items():
            if K.sha_file(os.path.join(reg_dir, f)) != s:
                return False, 'registry/%s 与登记时 sha 不同' % f
    return True, 'ok'


class Ctx(object):
    """一个 (结构, k0, kf) 上下文的全部算子；原生与 COMMON_SUPPORT 各一个实例。缓存与路径无关的量（父门、父名单、子名单、优先序）。"""

    def __init__(self, seg, st, k0, kf, kf2=None):
        self.seg, self.st, self.k0, self.kf, self.kf2 = seg, st, k0, kf, kf2
        self.parent = st.kept(k0[None, :])[0]
        self.sc0 = st.gate_scores(k0[None, :])[0]
        self.gp = st.gate_keep(self.sc0[None, :])[0]
        self.tid_ids = seg.tid[st.ids]
        self._c = {}
        self.facts = {}

    def cache(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    # ---- q 层
    def q_native(self, a):
        if self.kf2 is not None:                                     # SM：两分量 FALLBACK（E6j P 块同式）
            return self.cache(('qn', a), lambda: EN.blend(self.k0, [(0.5, self.kf[None, :]), (0.5, self.kf2[None, :])], a)[0])
        return self.cache(('qn', a), lambda: O.native_q(self.k0, self.kf, a))

    def child(self, a):
        return self.cache(('child', a), lambda: self.st.kept(self.q_native(a)[None, :])[0])

    def d_inc(self, gamma):
        return self.cache(('dinc', gamma), lambda: O.inc_d(self.seg, self.k0, self.kf, gamma))

    def q_base(self, base, a):
        if base == 'NATIVE':
            return self.q_native(a)
        return self.cache(('qinc1', a), lambda: O.inc_q(self.k0, self.d_inc(1.0), a))

    def s1_cells(self, q):
        s1 = np.zeros(self.seg.n, bool)
        s1[self.st.ids[self.st.gate_keep(self.st.gate_scores(q[None, :]))[0]]] = True
        return s1

    # ---- 调度
    def kept(self, op, a):
        st, seg, k0, kf = self.st, self.seg, self.k0, self.kf
        if op == 'PARENT':
            return self.parent
        if op == 'NATIVE':
            return self.child(a)
        if op in ('SZL3', 'SZL5'):
            return st.kept(O.szl_q(seg, k0, kf, a, int(op[3]))[None, :])[0]
        if op in ('SZL3_OWN', 'SZL5_OWN'):
            return st.kept(O.szl_own_q(seg, k0, kf, a, int(op[3]))[None, :])[0]
        if op in ('INC05', 'INC1'):
            return st.kept(O.inc_q(k0, self.d_inc(0.5 if op == 'INC05' else 1.0), a)[None, :])[0]
        if op == 'INC_SUPPORT0':
            return st.kept(O.inc_q(k0, self.d_inc(0.0), a)[None, :])[0]
        if op in ('INC_DOSE05', 'INC_DOSE1'):
            return st.kept(O.inc_q(k0, O.inc_dose_d(seg, k0, kf, 0.5 if op == 'INC_DOSE05' else 1.0), a)[None, :])[0]
        if op in TAUS:
            lists = self.cache(('rp', a), lambda: self._rp(a))
            return lists[TAUS[op]]
        if op.startswith('LX_'):
            _, lay, cell = op.split('_')
            L = self.cache(('lay', lay), lambda: O.lx_layers(seg, k0, lay))
            legal = self.cache('legal', st.legal)
            key0 = self.cache('key0', lambda: st.order_keys(k0, self.parent))
            key1 = self.cache(('key1', a), lambda: st.order_keys(self.q_native(a), self.child(a)))
            if cell == '10':
                return O.lx_select(seg, st, self.child(a), key0, L, legal)
            return O.lx_select(seg, st, self.parent, key1, L, legal)
        if op.startswith('HG_ONLY'):
            b = int(op[7:])
            g = O.hg_gate(st, self.sc0[None, :], b * st.bunit, self.tid_ids)
            return st.down(g)[0]
        if op.startswith('TREFIT'):
            g = 0.0 if op == 'TREFIT0' else 0.5
            s1_old = self.cache('s1_old', lambda: self.s1_cells(k0))
            s1_new = self.cache(('s1_new', a), lambda: self.s1_cells(self.q_native(a)))
            kk, nu = O.stage2_model(seg, st, s1_new, s1_new, (g, s1_old))
            self.facts[(op, a)] = dict(coef_interp_unavailable_days=nu)
            return kk & ~st.st.drop
        if op == 'POST2_INCREMENT':
            s1_old = self.cache('s1_old', lambda: self.s1_cells(k0))
            return O.post2_kept(seg, st, s1_old, k0, kf, a)
        if op.startswith('DOSE_'):
            return self._dose(op, a)
        base, rest = op.split('_', 1)                                  # BAND：NATIVE_SA5 / INC1_HG10 …
        kind, b = rest[:2], int(rest[2:])
        if kind == 'SA':
            q = O.sa_q_native(k0, kf, a, b) if base == 'NATIVE' else O.sa_q_inc(k0, self.d_inc(1.0), a, b)
            return st.kept(q[None, :])[0]
        return st.down(self.band_gate(base, kind, b, a)[None, :])[0]

    def band_gate(self, base, kind, b, a):
        def f():
            st = self.st
            sc1 = st.gate_scores(self.q_base(base, a)[None, :])[0]
            if kind == 'PM':
                gc = st.gate_keep(sc1[None, :])[0]
                return O.pm_gate(st, sc1, self.gp, gc, b * st.bunit, self.tid_ids)
            return O.hg_gate(st, sc1[None, :], b * st.bunit, self.tid_ids)[0]
        return self.cache(('gate', base, kind, b, a), f)

    def _dose(self, op, a):
        _, base, kb = op.split('_')
        kind, b = kb[:2], int(kb[2:])
        st, seg, k0, kf = self.st, self.seg, self.k0, self.kf
        if kind == 'SA':
            d = O.native_d(k0, kf) if base == 'NATIVE' else self.d_inc(1.0)
            at = O.sa_dose_alpha(seg, d, a, b)
            nod = None
        else:
            sc1 = st.gate_scores(self.q_base(base, a)[None, :])[0]
            gc = st.gate_keep(sc1[None, :])[0]
            at, nod = O.dose_alpha_from_edits(seg, st, self.band_gate(base, kind, b, a), gc, self.gp, a)
        q = O.native_q(k0, kf, at) if base == 'NATIVE' else O.inc_q(k0, self.d_inc(1.0), at)
        self.facts[(op, a)] = dict(no_dose_match_days=int(nod.sum()) if nod is not None else 0,
                                   mean_alpha_t=float(np.mean(at)))
        return st.kept(q[None, :])[0]

    def _rp(self, a):
        seg = self.seg
        child = self.child(a)
        tp = seg.SE.dev(seg.ci.t[self.parent], seg.ci.c[self.parent])
        wcell = np.zeros(seg.n)
        wcell[np.flatnonzero(self.parent)] = tp
        key1 = self.cache(('key1', a), lambda: self.st.order_keys(self.q_native(a), child))
        urank = O.rank_by_keys(seg, key1)
        lists, stats = O.rp_list(seg, self.parent, child, wcell, tuple(TAUS.values()), urank)
        for opn, tau in TAUS.items():
            s = stats[stats.tau == ('INF' if tau is None else tau)] if len(stats) else stats
            self.facts[(opn, a)] = dict(rp_days_with_edits=int(len(s)), rp_pairs=int(s.n_pairs.sum()) if len(s) else 0,
                                        rp_kept_pairs=int(s.n_keep.sum()) if len(s) else 0,
                                        rp_unknown_edits=int(s.unk.sum()) if len(s) else 0,
                                        rp_unpaired_structural=int((s.n_in + s.n_out - 2 * s.n_pairs - s.unk).sum()) if len(s) else 0,
                                        rp_solver=json.dumps(s.solver.value_counts().to_dict()) if len(s) else '{}',
                                        solver_limit_days=int(s.solver.astype(str).str.startswith('SOLVER_LIMIT').sum()) if len(s) else 0,
                                        rp_recovered_days=int(s.solver.astype(str).str.startswith('recovered').sum()) if len(s) else 0)
        return lists


def run(pname, task, reg_dir, out_dir, profile=False):
    t0 = time.time()
    mother, meas = task.split('|')
    if not profile:
        ok, why = registration_ok(reg_dir)
        if not ok:
            raise RuntimeError('登记门：%s' % why)
        K.post_gate(pname, 'run_det %s' % task)
    D = pd.read_csv(os.path.join(reg_dir, 'descriptors_E6k.csv'))
    A = pd.read_csv(os.path.join(reg_dir, 'accessory_E6k.csv'))
    D = D[D.task == task]
    A = A[A.task == task]
    seg = E.Seg(pname)
    acct = AC.Acct(seg)
    st = seg.struct(mother)
    k0 = st.q0
    t_env = time.time() - t0
    kf = kf2 = None
    if meas == 'SM':
        kf, kf2 = seg.kf('S'), seg.kf('M')
    elif meas != 'K0':
        kf = seg.kf(meas)
    if profile and kf is not None:                                    # 无真实新信息：当日内置换（只测时）
        rng = np.random.default_rng(K.stable_seed_int('E6k.profile', pname, task) % (2 ** 63))
        kf = _perm_within_day(seg, kf, rng)
        if kf2 is not None:
            kf2 = _perm_within_day(seg, kf2, rng)
    ctx = Ctx(seg, st, k0, kf if kf is not None else k0.copy(), kf2)
    tp = acct.target(ctx.parent)
    # ---- 目标清单：(目标 id, 算子, α, 上下文, H 列表, 描述符 id 列表)
    tgts = {}
    for r in D.itertuples():
        tgts.setdefault(r.target_id, dict(op=r.op, a=float(r.alpha), cs=False, Hs=set(), desc=[]))
        tgts[r.target_id]['Hs'].add(int(r.H))
        tgts[r.target_id]['desc'].append((r.desc_id, int(r.H)))
    for r in A.itertuples():
        cs = r.kind.startswith('COMMON_SUPPORT')
        tgts.setdefault(r.target_id, dict(op=r.op, a=float(r.alpha), cs=cs, Hs=set(), desc=[]))
        tgts[r.target_id]['Hs'].add(int(r.H))
        tgts[r.target_id]['desc'].append((r.acc_id, int(r.H)))
    cs_ctx = None
    if any(v['cs'] for v in tgts.values()):
        tc = time.time()
        J = np.isfinite(k0) & np.isfinite(kf)
        if kf2 is not None:
            J &= np.isfinite(kf2)
        k0J = seg.pct_on(seg.k0_raw(mother), J, 'hi')
        if profile:
            kfJ = np.where(J, kf, np.nan)
        else:
            kfJ = seg.pct_on(seg.raw(meas), J, E.MEAS[meas][2])
        stJ = seg.struct(mother, q0=k0J)
        cs_ctx = Ctx(seg, stJ, k0J, kfJ)
        t_cs = time.time() - tc
    else:
        t_cs = 0.0
    # ---- 逐目标
    DESC = {k: [] for k in AC.DESC_KEYS}
    TG = {k: [] for k in AC.TGT_KEYS}
    desc_ids, desc_tgt, desc_H, tgt_ids, bits, facts, prof = [], [], [], [], [], [], []
    wsave = {}
    fixed = set(D[D.primary144 | D.c1_hi | D.sm_anchor | (D.op == 'PARENT') | ((D.alpha == 0.25) & (D.H == 5))].target_id)
    for tid, v in tgts.items():
        tt0 = time.time()
        cx = cs_ctx if v['cs'] else ctx
        kept = cx.kept(v['op'], v['a'])
        t_op = time.time() - tt0
        tg = acct.target(kept)
        par_tg = acct.target(cx.parent) if v['cs'] else tp
        Hs = tuple(sorted(v['Hs']))
        is_par = v['op'] == 'PARENT'
        led = acct.ledgers(tg, Hs, par=None if is_par else par_tg, impact=not v['cs'], roll=not v['cs'])
        stt = acct.target_stats(tg, kept, None if is_par else cx.parent, None if is_par else par_tg)
        j = len(tgt_ids)
        tgt_ids.append(tid)
        for k in AC.TGT_KEYS:
            TG[k].append(stt[k])
        bits.append(np.packbits(kept))
        for did, H in v['desc']:
            desc_ids.append(did)
            desc_tgt.append(j)
            desc_H.append(H)
            for k in AC.DESC_KEYS:
                DESC[k].append(led[H][k])
        f = dict(target_id=tid, op=v['op'], alpha=v['a'], cs=v['cs'], n_cells=int(kept.sum()),
                 cells_vs_parent=int((kept != cx.parent).sum()))
        f.update(cx.facts.get((v['op'], v['a']), {}))
        facts.append(f)
        if tid in fixed:
            wsave[tid] = (tg['t'].astype(np.int32), tg['c'].astype(np.int32), tg['w'])
        prof.append(dict(target_id=tid, op=v['op'], op_s=round(t_op, 4), acct_s=round(time.time() - tt0 - t_op, 4), n_H=len(Hs)))
    # ---- 写出
    od = os.path.join(out_dir, pname)
    os.makedirs(od, exist_ok=True)
    stem = '%s__%s' % (mother, meas)
    p1 = os.path.join(od, '%s.npz' % stem)
    K.atomic_write_npz(p1, desc=np.array(desc_ids), desc_target=np.array(desc_tgt), desc_H=np.array(desc_H), targets=np.array(tgt_ids),
                       dates=np.array([str(d)[:10] for d in seg.dates]), n_cells=np.array([seg.n]),
                       bits=np.vstack(bits), **{'d_' + k: np.vstack(DESC[k]) for k in AC.DESC_KEYS},
                       **{'t_' + k: np.vstack(TG[k]) for k in AC.TGT_KEYS})
    p2 = os.path.join(od, 'weights_%s.npz' % stem)
    keys = sorted(wsave)
    off = np.r_[0, np.cumsum([len(wsave[k][0]) for k in keys])]
    K.atomic_write_npz(p2, targets=np.array(keys), off=off,
                       t=np.concatenate([wsave[k][0] for k in keys]) if keys else np.zeros(0, np.int32),
                       c=np.concatenate([wsave[k][1] for k in keys]) if keys else np.zeros(0, np.int32),
                       w=np.concatenate([wsave[k][2] for k in keys]) if keys else np.zeros(0))
    p3 = os.path.join(od, 'facts_%s.csv' % stem)
    K.atomic_write_csv(p3, pd.DataFrame(facts))
    p4 = os.path.join(od, 'profile_%s.csv' % stem)
    K.atomic_write_csv(p4, pd.DataFrame(prof))
    wall = time.time() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0
    if not profile:
        K.write_receipt('run_det_%s_%s' % (pname, stem), [p1, p2, p3, p4], 'SUCCEEDED', n_desc=len(desc_ids), n_targets=len(tgt_ids),
                        wall_s=round(wall, 1), env_s=round(t_env, 1), cs_s=round(t_cs, 1), maxrss_gb=round(rss, 2))
    print('%s %s: %d 描述符 / %d 目标；wall %.0fs（env %.0fs，CS %.0fs）；maxrss %.1f GB' % (pname, task, len(desc_ids), len(tgt_ids), wall, t_env,
                                                                                    t_cs, rss), flush=True)
    return 0


def _perm_within_day(seg, v, rng):
    out = v.copy()
    ok = np.isfinite(v)
    for d in range(seg.T):
        a0, a1 = seg.off[d], seg.off[d + 1]
        ix = np.arange(a0, a1)[ok[a0:a1]]
        out[ix] = v[rng.permutation(ix)]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--task', required=True)
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--reg', default=None)
    a = ap.parse_args()
    if a.profile:
        reg = a.reg or os.path.join(K.TRIAL, 'a0', 'registry')
        out = os.path.join(K.TRIAL, 'profile_det')
    else:
        reg = K.P('registry')
        out = K.P('accounts')
    return run(a.segment, a.task, reg, out, profile=a.profile)


if __name__ == '__main__':
    sys.exit(main())
