# -*- coding: utf-8 -*-
"""E6l 确定性账户（brief §1.4 / §5；plan §5–§9.3a）。一段一个父进程：段环境与所需测量只加载一次 → fork 进程池；任务 = (母体, 测量)：
该 (母体, 测量) 的全部登记描述符 + 该任务的附属（KERNEL_DOSE / 支持桥 CSC · CSP · MQ0 / STRICT250_STATE / INV_CAP_LOOP_PAIR）。
两阶段（brief §1.4：Stage A 掩码事实在任何收益计算之前落盘）：
  --phase masks     名单与目标层统计（DEV 权重、size 紧区间、编辑、lv5；不算任何收益）+ 门层记忆事实 / 库存事实 / 测量事实
                    → masks/<段>/<母体>__<测量>.npz（targets / bits / t_*）+ mfacts_<…>.csv；登记门 = A0 清单存在且 registry sha 一致
  --phase accounts  读 masks 的名单 → DEV → 稀疏账本（H 列表；与 E6k Acct 同构对象逐值相同）→ accounts/<段>/<母体>__<测量>.npz
                    （desc × 日 DESC_KEYS；目标 × 日 TGT_KEYS；位图）+ weights_<…>.npz（固定权重目标）；登记门 = P / B 两包 + 后段 post_gate
目标与 H 无关（INV 例外：按 H 递推、目标 ID 含 H，plan §5.5）；测量 K0 = 母体原 K（PARENT 与旧 K 规则，α0）。
附属：KD = k0 + α·d_dose（C 外回旧 K；e6l_ops.kernel_dose）；CSC / CSP = 新测量 / Q0 在共同支持上重做源中性化与秩（SegL.common_support）；
MQ0 = Q0 坏度遮罩到新测量支持；S250 = 调度用 STRICT250 状态；ICL = INV 闭环同资本（p* = min(子提议, 父资本) = 0 的日不进库存），
ICL 行的 sc_child / sc_parent = 本对缩放后的子 / 父（ICLPAR 行 = 其 sc_parent）。
--profile：新测量换成当日内置换（只测时 / 资源），读 TRIAL 试编 registry，写 TRIAL，不写回执。"""
import e6l_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource
import multiprocessing as mp

import numpy as np
import pandas as pd

import e6l_core as L
import e6l_env as V
import e6l_ops as O
import e6l_registry as RG
import e6k_ops as KO
import e6k_acct as AC

CTX = {}
ACC_TAGS = {'KD': 'KERNEL_DOSE', 'CSC': 'SUPPORT_CS_CHILD', 'CSP': 'SUPPORT_CS_PARENT', 'MQ0': 'SUPPORT_MASKQ0', 'S250': 'STRICT250_STATE',
            'ICL': 'INV_CAP_LOOP_PAIR'}


def registration_ok(reg_dir, phase='accounts'):
    """masks：A0 清单 registry sha 一致；accounts / 随机：P / B 两包清单 registry sha 一致。"""
    names = ['a0_manifest_E6l.json'] if phase == 'masks' else [L.MANIFEST_P, L.MANIFEST_B]
    for nm in names:
        p = L.P('registration', nm)
        if not os.path.exists(p):
            return False, '%s 未登记' % nm
        m = json.load(open(p, encoding='utf-8'))
        for f, s in m['registry_sha256'].items():
            q = os.path.join(reg_dir, f)
            if os.path.exists(q) and L.sha_file(q) != s:
                return False, 'registry/%s 与登记时 sha 不同' % f
    return True, 'ok'


def perm_within_day(seg, v, rng):
    out = v.copy()
    ok = np.isfinite(v)
    for d in range(seg.T):
        a0, a1 = seg.off[d], seg.off[d + 1]
        ix = np.arange(a0, a1)[ok[a0:a1]]
        out[ix] = v[rng.permutation(ix)]
    return out


class DetCtx(object):
    """一个 (结构, k0, kf) 上下文：门分数、无带门、各规则名单；缓存与路径无关的量。"""

    def __init__(self, seg, st, k0, kf, meas):
        self.seg, self.st, self.k0, self.kf, self.meas = seg, st, k0, kf, meas
        self.parent = st.kept(k0[None, :])[0]
        self.sc0 = st.gate_scores(k0[None, :])[0]
        self.gp = st.gate_keep(self.sc0[None, :])[0]
        self._c = {}
        self.facts = {}

    def cache(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    def q(self, a, var=None):
        seg, k0 = self.seg, self.k0
        if var is None:
            if a == 0 or self.kf is None:
                return k0
            return self.cache(('q', a), lambda: KO.native_q(k0, self.kf, a))
        if var == 'KD':
            def f():
                kq0 = seg.meas_kf('Q0')
                dd, status = O.kernel_dose(seg, k0, kq0, self.kf)
                C = np.isfinite(k0) & np.isfinite(kq0) & np.isfinite(self.kf)
                vals, cnts = np.unique(status, return_counts=True)
                self.facts[('KD_status',)] = dict(zip([str(v) for v in vals], [int(c) for c in cnts]))
                return np.where(C, k0 + a * dd, k0)
            return self.cache(('KD', a), f)
        if var in ('CSC', 'CSP'):
            kX, kQ, C = seg.common_support(self.meas)
            return self.cache((var, a), lambda: KO.native_q(k0, kX if var == 'CSC' else kQ, a))
        if var == 'MQ0':
            kq0 = seg.meas_kf('Q0')
            return self.cache(('MQ0', a), lambda: KO.native_q(k0, np.where(np.isfinite(self.kf), kq0, np.nan), a))
        raise ValueError(var)

    def sc(self, a, var=None):
        if (a == 0 or self.kf is None) and var is None:
            return self.sc0
        return self.cache(('sc', a, var), lambda: self.st.gate_scores(self.q(a, var)[None, :])[0])

    def U(self, a, var=None):
        if (a == 0 or self.kf is None) and var is None:
            return self.gp
        return self.cache(('U', a, var), lambda: self.st.gate_keep(self.sc(a, var)[None, :])[0])

    def b_day(self, rule, strict=False):
        if rule['kind'] == 'STATE':
            return self.seg.state_b(rule['schedule'], strict=strict)
        return np.full(self.seg.T, rule['b'])

    def final(self, op, a, H=None, var=None, strict=False, loop_cap=None, tag=None):
        rule = O.parse_op(op)
        st = self.st
        if rule['kind'] == 'NATIVE':
            if (a == 0 or self.kf is None) and var is None:
                return self.parent
            return self.cache(('native', a, var), lambda: st.down(self.U(a, var)[None, :])[0])
        if rule['kind'] == 'INV':
            G, F, stt, rec = O.inv_path(st, self.sc(a, var)[None, :], self.U(a, var)[None, :], rule['b'], int(H), loop_parent_cap=loop_cap, record=True)
            self.facts[tag] = inv_facts(rec)
            return F[0]
        G, stt, rec = O.mem_gate(st, self.sc(a, var)[None, :], self.U(a, var)[None, :], rule, b_day=self.b_day(rule, strict), record=True)
        self.facts[tag] = gate_facts(G[0], self.U(a, var), st, rec)
        return st.down(G)[0]


def gate_facts(G, U, st, rec):
    """门层记忆事实（Stage A；plan §5.2 / 附录 B）：靠 bonus 续选份额、连续依靠 bonus 日数、自然重确认年龄、成员留存率。"""
    dom = st.dom
    rel = G & ~U
    n_g = max(int(G.sum()), 1)
    seg = st.seg
    cols = seg.ci.c[st.ids]
    run = np.zeros(seg.Nc, np.int64)
    runs = []
    age = np.full(seg.Nc, -1, np.int64)
    ages = []
    prevg = np.zeros(seg.Nc, bool)
    kept_n = kept_d = 0
    for d in range(seg.T):
        a, b = dom.off[d], dom.off[d + 1]
        if b == a or dom.K[d] == 0:
            run[:] = 0
            age[:] = -1
            prevg[:] = False
            continue
        cc = cols[a:b]
        r = rel[a:b]
        u = U[a:b]
        g = G[a:b]
        if prevg.any():
            kept_n += int((prevg[cc] & g).sum())
            kept_d += int(prevg.sum())
        newrun = np.zeros(seg.Nc, np.int64)
        newrun[cc[r]] = run[cc[r]] + 1
        run = newrun
        newage = np.full(seg.Nc, -1, np.int64)
        newage[cc[u]] = 0
        keep = g & ~u & (age[cc] >= 0)
        newage[cc[keep]] = age[cc[keep]] + 1
        age = newage
        prevg = np.zeros(seg.Nc, bool)
        prevg[cc[g]] = True
        if r.any():
            runs.append(run[cc[r]])
        if g.any():
            ages.append(age[cc[g]])
    rr = np.concatenate(runs) if runs else np.zeros(0)
    aa = np.concatenate(ages) if ages else np.zeros(0)

    def q(x, p):
        return float(np.percentile(x, p)) if len(x) else float('nan')
    return dict(bonus_reliant_share=float(rel.sum()) / n_g, reliant_run_p50=q(rr, 50), reliant_run_p90=q(rr, 90),
                reliant_run_max=float(rr.max()) if len(rr) else 0.0, confirm_age_p50=q(aa, 50), confirm_age_p90=q(aa, 90),
                confirm_age_max=float(aa.max()) if len(aa) else 0.0, gate_retention=float(kept_n / kept_d) if kept_d else float('nan'),
                gate_days=int(rec['days']) if rec else 0, bonus_rows=int(rec['bonus_rows']) if rec else 0)


def inv_facts(rec):
    d = max(rec['days'], 1)
    return dict(inv_mark_coverage=float(rec['marked'][0] / max(rec['dom_cells'][0], 1)), inv_saturated_day_share=float(rec['saturated_days'][0] / d),
                gate_days=int(rec['days']), bonus_days=int(rec['bonus_days']))


def task_targets(D, A, task):
    """该任务的目标表：target_key → dict(op, a, H(INV), var, strict, loop, Hs, desc[(id, H)])。"""
    tg = {}
    for r in D[D.task == task].itertuples():
        H = int(r.H)
        tid = r.target_id
        v = tg.setdefault(tid, dict(op=r.op, a=float(r.alpha), H=H if r.op == 'INV10' else None, var=None, strict=False, loop=False,
                                    Hs=set(), desc=[], fixed=bool(r.fixed_weights)))
        v['Hs'].add(H)
        v['desc'].append((r.desc_id, H))
        v['fixed'] |= bool(r.fixed_weights)
    for r in A[A.task == task].itertuples():
        tag = r.acc_id.split('|', 1)[0]
        if tag not in ACC_TAGS:
            continue
        H = int(r.H)
        base = (r.meas, r.mother, float(r.alpha), H, r.op)
        tid = '%s|%s' % (tag, RG.target_of(base)) if tag != 'ICL' else r.acc_id
        v = tg.setdefault(tid, dict(op=r.op, a=float(r.alpha), H=H if r.op == 'INV10' else None,
                                    var=tag if tag in ('KD', 'CSC', 'CSP', 'MQ0') else None, strict=tag == 'S250', loop=tag == 'ICL',
                                    Hs=set(), desc=[], fixed=False))
        v['Hs'].add(H)
        v['desc'].append((r.acc_id, H))
    return tg


def load_ctx(pname, tasks, profile, reg_dir):
    t0 = time.time()
    seg = V.SegL(pname)
    acct = AC.Acct(seg)
    kfs = {}
    for task in tasks:
        m = task.split('|')[1]
        if m != 'K0' and m not in kfs:
            kf = seg.meas_kf(m)
            if profile:
                rng = np.random.default_rng(L.stable_seed_int('E6l.profile', pname, m) % (2 ** 63))
                kf = perm_within_day(seg, kf, rng)
            kfs[m] = kf
    if any(m.split('|')[1] in V.QNEW + V.QRANK for m in tasks):
        seg.meas_kf('Q0')
    for form in V.E.P8:
        seg.struct(form)
    CTX.update(seg=seg, acct=acct, kfs=kfs, pname=pname, profile=profile, t_env=time.time() - t0,
               D=L.read_csv_keep(os.path.join(reg_dir, "descriptors_E6l.csv")), A=L.read_csv_keep(os.path.join(reg_dir, "accessory_E6l.csv")))


def run_task(args):
    try:
        return _run_task(*args)
    except Exception as e:                                                   # noqa: BLE001
        import traceback
        return ('FAILED', '%s %s: %s\n%s' % (args[0], type(e).__name__, e, traceback.format_exc()[-2500:]))


def _run_task(task, phase, reg_dir, out_dir, write_receipt):
    t0 = time.time()
    seg, acct, pname = CTX['seg'], CTX['acct'], CTX['pname']
    mother, meas = task.split('|')
    st = seg.struct(mother)
    k0 = st.q0
    kf = CTX['kfs'].get(meas)
    ctx = DetCtx(seg, st, k0, kf, meas)
    stem = '%s__%s' % (mother, meas)
    D = CTX["D"]
    A = CTX["A"]
    TG = task_targets(D, A, task)
    tp = acct.target(ctx.parent)
    pcap = np.bincount(tp['t'], weights=tp['w'], minlength=seg.T)
    if phase == 'masks':
        tgt_ids, bits, facts, prof = [], [], [], []
        TS = {k: [] for k in AC.TGT_KEYS}
        for tid, v in TG.items():
            tt0 = time.time()
            kept = ctx.final(v['op'], v['a'], v['H'], var=v['var'], strict=v['strict'], loop_cap=pcap if v['loop'] else None, tag=tid)
            t_op = time.time() - tt0
            tg = acct.target(kept)
            is_par = (v['op'] == 'NATIVE' and v['a'] == 0 and v['var'] is None)
            stt = acct.target_stats(tg, kept, None if is_par else ctx.parent, None if is_par else tp)
            for k in AC.TGT_KEYS:
                TS[k].append(stt[k])
            tgt_ids.append(tid)
            bits.append(np.packbits(kept))
            f = dict(target_id=tid, op=v['op'], alpha=v['a'], H_state=v['H'] if v['H'] is not None else 'NOT_APPLICABLE',
                     variant=v['var'] or ('S250' if v['strict'] else ('ICL' if v['loop'] else 'REGISTERED')),
                     n_cells=int(kept.sum()), cells_vs_parent=int((kept != ctx.parent).sum()),
                     cells_vs_native=int((kept != ctx.final('NATIVE', v['a'])).sum()) if (v['a'] != 0 and kf is not None) else 0,
                     cap_zero_days_loop=int(((pcap <= 0) & (np.bincount(seg.ci.t[kept], minlength=seg.T) > 0)).sum()) if v['loop'] else 0)
            f.update(ctx.facts.get(tid, {}))
            if v['var'] == 'KD':
                f['kd_status'] = json.dumps(ctx.facts.get(('KD_status',), {}), ensure_ascii=False)
            facts.append(f)
            prof.append(dict(target_id=tid, op=v['op'], op_s=round(t_op, 4), stats_s=round(time.time() - tt0 - t_op, 4)))
        od = os.path.join(out_dir, pname)
        os.makedirs(od, exist_ok=True)
        p1 = os.path.join(od, '%s.npz' % stem)
        L.atomic_write_npz(p1, targets=np.array(tgt_ids), bits=np.vstack(bits), n_cells=np.array([seg.n]),
                           dates=np.array([str(d)[:10] for d in seg.dates]), **{'t_' + k: np.vstack(TS[k]) for k in AC.TGT_KEYS})
        p2 = os.path.join(od, 'mfacts_%s.csv' % stem)
        F = pd.DataFrame(facts)
        mf = seg.mfacts.get(meas, {})
        for k, val in mf.items():
            F['meas_' + k] = val
        L.atomic_write_csv(p2, F)
        p3 = os.path.join(od, 'profile_%s.csv' % stem)
        L.atomic_write_csv(p3, pd.DataFrame(prof))
        outs = [p1, p2, p3]
        n_desc = sum(len(v['desc']) for v in TG.values())
    else:
        mz = L.npz(os.path.join(L.P('masks') if not CTX['profile'] else os.path.join(L.TRIAL, 'profile_masks'), pname, '%s.npz' % stem))
        mt = [str(x) for x in mz['targets']]
        if set(mt) != set(TG):
            raise RuntimeError('masks 目标集合与登记不符：%s' % sorted(set(mt) ^ set(TG))[:5])
        DESC = {k: [] for k in AC.DESC_KEYS}
        desc_ids, desc_tgt, desc_H, prof = [], [], [], []
        wsave = {}
        n = seg.n
        for j, tid in enumerate(mt):
            v = TG[tid]
            tt0 = time.time()
            kept = np.unpackbits(mz['bits'][j])[:n].astype(bool)
            tg = acct.target(kept)
            Hs = tuple(sorted(v['Hs']))
            is_par = (v['op'] == 'NATIVE' and v['a'] == 0 and v['var'] is None)
            led = acct.ledgers(tg, Hs, par=None if is_par else tp, impact=True, roll=True)
            for did, H in v['desc']:
                desc_ids.append(did)
                desc_tgt.append(j)
                desc_H.append(H)
                for k in AC.DESC_KEYS:
                    DESC[k].append(led[H][k])
                if v['loop']:                                                # ICLPAR：本对缩放父
                    desc_ids.append('ICLPAR|' + did.split('|', 1)[1])
                    desc_tgt.append(j)
                    desc_H.append(H)
                    for k in AC.DESC_KEYS:
                        DESC[k].append(led[H]['sc_parent'] if k == 'net8' else np.full(seg.T, np.nan))
            if v['fixed']:
                wsave[tid] = (tg['t'].astype(np.int32), tg['c'].astype(np.int32), tg['w'])
            prof.append(dict(target_id=tid, acct_s=round(time.time() - tt0, 4), n_H=len(Hs)))
        od = os.path.join(out_dir, pname)
        os.makedirs(od, exist_ok=True)
        p1 = os.path.join(od, '%s.npz' % stem)
        L.atomic_write_npz(p1, desc=np.array(desc_ids), desc_target=np.array(desc_tgt), desc_H=np.array(desc_H), targets=np.array(mt),
                           dates=mz['dates'], n_cells=mz['n_cells'], bits=mz['bits'], **{'d_' + k: np.vstack(DESC[k]) for k in AC.DESC_KEYS},
                           **{k: mz[k] for k in mz if k.startswith('t_')})
        keys = sorted(wsave)
        off = np.r_[0, np.cumsum([len(wsave[k][0]) for k in keys])]
        p2 = os.path.join(od, 'weights_%s.npz' % stem)
        L.atomic_write_npz(p2, targets=np.array(keys), off=off,
                           t=np.concatenate([wsave[k][0] for k in keys]) if keys else np.zeros(0, np.int32),
                           c=np.concatenate([wsave[k][1] for k in keys]) if keys else np.zeros(0, np.int32),
                           w=np.concatenate([wsave[k][2] for k in keys]) if keys else np.zeros(0))
        p3 = os.path.join(od, 'profile_%s.csv' % stem)
        L.atomic_write_csv(p3, pd.DataFrame(prof))
        outs = [p1, p2, p3]
        n_desc = len(desc_ids)
    wall = time.time() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0
    rec = None
    if write_receipt:
        rec = L.write_receipt('run_det_%s_%s_%s' % (phase, pname, stem), outs, 'SUCCEEDED', n_desc=n_desc, n_targets=len(TG), wall_s=round(wall, 1),
                              maxrss_gb=round(rss, 2), code_sha256={f: L.sha_file(os.path.join(L.CODE, f))[:16] for f in
                                                                    ('e6l_run_det.py', 'e6l_ops.py', 'e6l_env.py', 'e6l_state.py', 'e6l_core.py')})
    return ('SUCCEEDED', dict(task=task, n_desc=n_desc, n_targets=len(TG), wall=round(wall, 1), rss=round(rss, 2)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True)
    ap.add_argument('--phase', required=True, choices=('masks', 'accounts'))
    ap.add_argument('--tasks', default='ALL')
    ap.add_argument('--workers', type=int, default=24)
    ap.add_argument('--profile', action='store_true')
    ap.add_argument('--reg', default=None)
    a = ap.parse_args()
    pname = a.segment
    if a.profile:
        reg = a.reg or os.path.join(L.TRIAL, 'a0', 'registry')
        out = os.path.join(L.TRIAL, 'profile_masks' if a.phase == 'masks' else 'profile_det')
    else:
        reg = L.P('registry')
        out = L.P('masks' if a.phase == 'masks' else 'accounts')
        ok, why = registration_ok(reg, a.phase)
        if not ok:
            raise RuntimeError('登记门：%s' % why)
        L.post_gate(pname, 'run_det %s %s' % (a.phase, pname))
    D = L.read_csv_keep(os.path.join(reg, 'descriptors_E6l.csv'), usecols=['task'])
    tasks = sorted(D.task.unique()) if a.tasks == 'ALL' else a.tasks.split(',')
    load_ctx(pname, tasks, a.profile, reg)
    print('%s %s：%d 任务；环境 %.0fs；maxrss %.1f GB' % (pname, a.phase, len(tasks), CTX['t_env'],
                                                    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0), flush=True)
    heavy = {m: i for i, m in enumerate(('Q0', 'Q_D5', 'C1', 'K0', 'Q_RANK5'))}
    tasks = sorted(tasks, key=lambda t: heavy.get(t.split('|')[1], 9))
    jobs = [(t, a.phase, reg, out, not a.profile) for t in tasks]
    bad = 0
    t0 = time.time()
    with mp.get_context('fork').Pool(a.workers, maxtasksperchild=8) as pool:
        for stt, info in pool.imap_unordered(run_task, jobs):
            if stt != 'SUCCEEDED':
                bad += 1
                print('FAILED', info, flush=True)
            else:
                print('done %s desc %d targets %d wall %.0fs rss %.1fGB' % (info['task'], info['n_desc'], info['n_targets'], info['wall'], info['rss']),
                      flush=True)
    print('ALL_DONE %s %s bad=%d wall %.0fs' % (pname, a.phase, bad, time.time() - t0), flush=True)
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
