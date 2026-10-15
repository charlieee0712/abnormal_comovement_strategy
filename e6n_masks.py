# -*- coding: utf-8 -*-
"""E6n 名单层（brief §1.3-2 / -6 / -7；plan §6.2–§6.4a）。不读收益、不算 DEV / 账本。
一个进程 = (段, 母体)。真实段结构 e6l_env.SegL（源 build_period 重建段上下文，与 E6m 阶段 S 同）→ Struct；
名单键 = (记忆, α, 输入变体[, 分量控制变体])，键内与 H 无关（H 只影响账本）；每键算一次：
  K：NATIVE = st.q0（α = 0）；Q0 / C1 / FACET / RAW / CLONE / CLONE_RAW → native_q(st.q0, kf, α)；DOSE / CDOSE → e6n_vars.dose_K / cdose_K
  → 源门分 st.gate_scores → 门保留 st.gate_keep → 记忆门（源 e6l_ops.mem_gate；HG = 本账户上一形成日实际门名单，LAG1 = 本算子昨日自然名单）
  → 下游 st.down（源函数）→ 最终名单。
身份（Stage 0 A3-8 子项，每进程开头实核，不过即停）：段单元坐标 = 测量单元；st.q0 = 测量 k0（pcond 单元）；meas_kf('Q0') = 测量 kQ（逐位）。
输出 masks/<段>/<母体>.npz（mask_keys、final_bits、gate_bits、n_cells）+ facts_<母体>.csv。"""
import os
import sys
import json
import time
import hashlib
import argparse
import resource

import numpy as np
import pandas as pd

import e6n_core as N
import e6n_vars as VR

PARENTS6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')


def mask_key(memory, alpha, variant, ctrl=None):
    k = '%s|a%s|%s' % (memory, VR_fnum(alpha), variant)
    return k + ('|ctrl:' + ctrl if ctrl else '')


def VR_fnum(x):
    return '%g' % float(x)


def registry_rows():
    rd = lambda n: pd.read_csv(N.P('registry', n), keep_default_na=False)
    D = rd('descriptors_E6n.csv')
    A = rd('auxiliary_E6n.csv')
    C = rd('component_controls_E6n.csv')
    var_of = dict(zip(D.desc_id, D.input_variant))
    var_of.update(dict(zip(C.comp_id, C.input_variant)))
    rows = []
    for r in D.itertuples():
        rows.append(dict(obj=r.desc_id, table='MAIN', parent=r.parent, memory=r.memory, alpha=float(r.outer_alpha), H=int(r.H),
                         variant=r.input_variant, ctrl=None))
    for r in A.itertuples():
        rows.append(dict(obj=r.aux_id, table='AUX', parent=r.parent, memory=r.memory, alpha=float(r.outer_alpha), H=int(r.H),
                         variant=r.input_variant, ctrl=None))
    for r in C.itertuples():
        ctrl = var_of.get(r.input_control_desc_id) if r.kind == 'COMPONENT_DOSE' else None
        if r.kind == 'COMPONENT_DOSE' and not ctrl:
            raise RuntimeError('COMPONENT_DOSE 找不到分量控制变体：%s' % r.comp_id)
        rows.append(dict(obj=r.comp_id, table='COMP', parent=r.parent, memory=r.memory, alpha=float(r.outer_alpha), H=int(r.H),
                         variant=r.input_variant, ctrl=ctrl))
    R = pd.DataFrame(rows)
    R['alpha_eff'] = np.where(R.variant.str.startswith('NATIVE'), 0.0, R.alpha)
    R['mask_key'] = [mask_key(m, a, v, c) for m, a, v, c in zip(R.memory, R.alpha_eff, R.variant, R.ctrl)]
    return R


def source_mem_gate(st, sc, U, memory):
    """源 e6l_ops.mem_gate（e6m_s_real.source_mem_gate_s 同式）：HG10 / LAG1_10，b = 10（× st.bunit）。"""
    import e6l_ops as LO
    op = {'HG10': 'HG10', 'LAG1_10': 'LAG1_10'}[memory]
    G, stt, _ = LO.mem_gate(st, sc, U, LO.parse_op(op), b_day=np.full(st.seg.T, 10.0))
    return G


class Runner(object):
    def __init__(self, seg_name, parent):
        import e6l_env as V
        t0 = time.time()
        self.seg_name, self.parent = seg_name, parent
        self.seg = V.SegL(seg_name, state=False)
        self.st = self.seg.struct(parent)
        self.B = VR.Base(seg_name)
        self.ident = self.identity()
        self.t_load = round(time.time() - t0, 1)
        self._down = {}
        self._kf = {}

    def identity(self):
        seg, B = self.seg, self.B
        out = dict(cells_equal=bool(np.array_equal(seg.ci.t, B.t) and np.array_equal(seg.ci.c, B.c)))
        if not out['cells_equal']:
            raise RuntimeError('段单元坐标与测量单元不一致')
        if self.parent in PARENTS6:
            k0 = B.get('k0')
            q0 = np.asarray(self.st.q0, float)
            fin = np.isfinite(k0) & np.isfinite(q0)
            out['k0_eq_st_q0'] = bool((np.isfinite(k0) == np.isfinite(q0)).all() and (k0[fin] == q0[fin]).all())
            kq = np.asarray(seg.meas_kf('Q0'), float)
            fq = np.isfinite(kq) & np.isfinite(B.kQ)
            out['kQ_eq_meas_kf_Q0'] = bool((np.isfinite(kq) == np.isfinite(B.kQ)).all() and (kq[fq] == B.kQ[fq]).all())
            if not (out['k0_eq_st_q0'] and out['kQ_eq_meas_kf_Q0']):
                raise RuntimeError('身份不符：%s' % out)
        return out

    def kf(self, variant):
        if variant not in self._kf:
            if variant == 'C1':
                self._kf[variant] = (np.asarray(self.seg.meas_kf('C1'), float), np.zeros(self.B.n, bool))
            else:
                self._kf[variant] = VR.variant_kf(self.B, variant)
        return self._kf[variant]

    def K_of(self, variant, alpha, ctrl):
        st, B = self.st, self.B
        q0 = np.asarray(st.q0, float)
        f = variant.split('|')[0]
        if f == 'NATIVE':
            return q0, {}
        if f in ('DOSE', 'CDOSE'):
            ov = variant.split('|', 1)[1]
            kfo, act = self.kf(ov)
            if f == 'DOSE':
                return VR.dose_K(q0, B.kQ, kfo, act, alpha, B.t)
            kfc, _ = self.kf(ctrl)
            return VR.cdose_K(q0, B.kQ, kfo, kfc, act, alpha, B.t)
        kf, act = self.kf(variant)
        return VR.native_q(q0, kf, alpha), dict(active_cells=int(act.sum()))

    def down(self, G):
        h = hashlib.sha1(np.packbits(G).tobytes()).hexdigest()
        if h not in self._down:
            self._down[h] = self.st.down(G[None, :])[0]
        return self._down[h]

    def run(self, keys):
        st = self.st
        rows, finals, gates = [], [], []
        F0 = None
        for mk in keys:
            t1 = time.time()
            p = mk.split('|ctrl:')
            ctrl = p[1] if len(p) > 1 else None
            memory, a, variant = p[0].split('|', 2)
            alpha = float(a[1:])
            K, info = self.K_of(variant, alpha, ctrl)
            sc = st.gate_scores(K[None, :])
            U = st.gate_keep(sc)
            G = U if memory == 'NONE' else source_mem_gate(st, sc, U, memory)
            F = self.down(G[0])
            if variant.startswith('NATIVE') and memory == 'NONE':
                F0 = F
            finals.append(np.packbits(F))
            gates.append(np.packbits(G[0]))
            rows.append(dict(mask_key=mk, memory=memory, alpha=alpha, variant=variant, ctrl=ctrl or 'NOT_APPLICABLE',
                             gate_members=int(G[0].sum()), final_members=int(F.sum()), reliant=int((G[0] & ~U[0]).sum()),
                             seconds=round(time.time() - t1, 2), **{k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in info.items()}))
        R = pd.DataFrame(rows)
        if F0 is not None:
            R['final_vs_native'] = [int((np.unpackbits(b)[:self.seg.n].astype(bool) != F0).sum()) for b in finals]
        return R, finals, gates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--parent', required=True)
    ap.add_argument('--limit', type=int, default=0, help='试跑：只算前 k 个键（键按登记顺序）')
    a = ap.parse_args()
    t0 = time.time()
    R = registry_rows()
    R = R[R.parent == a.parent]
    keys = list(dict.fromkeys(sorted(R.mask_key, key=lambda k: (0 if k.split('|', 2)[2].startswith('NATIVE') else 1, k))))
    if a.limit:
        keys = keys[:a.limit]
    run = Runner(a.seg, a.parent)
    Rk, finals, gates = run.run(keys)
    od = N.P('masks' if not a.limit else 'masks_pilot', a.seg)
    os.makedirs(od, exist_ok=True)
    p = os.path.join(od, '%s.npz' % a.parent)
    N.atomic_write_npz(p, mask_keys=np.array([str(k) for k in Rk.mask_key], dtype='U'), final_bits=np.array(finals), gate_bits=np.array(gates), n_cells=np.array([run.seg.n]))
    pf = os.path.join(od, 'facts_%s.csv' % a.parent)
    N.atomic_write_csv(pf, Rk)
    N.atomic_write_json(os.path.join(od, 'identity_%s.json' % a.parent), dict(run.ident, t_load=run.t_load))
    N.write_receipt('E6n_masks_%s_%s%s' % (a.seg, a.parent, '_pilot' if a.limit else ''), [p, pf], code=[__file__, VR.__file__],
                    keys=len(keys), wall_s=round(time.time() - t0, 1), t_load=run.t_load,
                    rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2), identity=run.ident)
    print(json.dumps(dict(seg=a.seg, parent=a.parent, keys=len(keys), wall_s=round(time.time() - t0, 1), t_load=run.t_load, identity=run.ident),
                     ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
