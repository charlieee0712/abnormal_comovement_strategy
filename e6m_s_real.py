# -*- coding: utf-8 -*-
"""E6m 阶段 S 的结构工厂与目录约定（mock / 真实两种模式共用同一套算子与输出格式）。
- struct = 'mock'：e6m_s_mock.MockSeg（B2 开发；六形态；C1 / M / S = SOURCE_WAIT；R2 / A06 = OUT_OF_SCOPE_MOCK）；输出根 stageS_dev/。
- struct = 'real'：真实 e6l_env.SegL 的适配视图（阶段 S；需要 X01 与 E6i / E6j 缓存），补齐 mock 同名属性
  （pool0 / ccols / ccolnames / cells / to_tn），八形态全有，C1 / M / S 取引擎 meas_kf；输出根 = 工作目录顶层。
- 测量：Q0 —— mock 用本轮云机 kQ0（meas），真实用引擎 meas_kf('Q0')（Stage 0 S A2-5 核两者逐位）；两日测量与 V 两种模式都用本轮 meas。
- 记忆门：mock 用转录 e6m_s_ops.src_mem_gate；真实用源 e6l_ops.mem_gate（Stage 0 S 核两者逐位：mock 上 AST 抽取 24 / 24，真实结构上 import 再核）。
单元坐标两种模式相同（pool0 单元 (t, c) 字典序）——Stage 0 S structid 逐位核。"""
import os

import numpy as np

import e6m_core as M

TWO = ('Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2')


class RealSeg(object):
    """真实段的 mock 同名视图（只读；其余属性透传给 e6l_env.SegL）。"""

    def __init__(self, pname):
        import e6l_env as V
        self._s = V.SegL(pname, state=False)
        S = self._s.S
        self.pname = pname
        self.pool0 = S.pool0
        self.ccols = np.asarray(S.ccols)
        self.ccolnames = np.array([str(x) for x in S.ccolnames])

    def __getattr__(self, k):
        return getattr(self._s, k)

    def cells(self, A):
        return np.asarray(A)[:, self.ccols][self.ci.t, self.ci.c]

    def to_tn(self, G_cells):
        out = np.zeros(self.pool0.shape, bool)
        ix = np.flatnonzero(G_cells)
        out[self.ci.t[ix], self.ccols[self.ci.c[ix]]] = True
        return out

    def struct(self, form):
        return self._s.struct(form)


def seg_of(pname, struct):
    if struct == 'mock':
        import e6m_s_mock as MK
        return MK.MockSeg(pname)
    if struct == 'real':
        return RealSeg(pname)
    raise ValueError(struct)


def root(struct, *parts):
    return M.P('stageS_dev', *parts) if struct == 'mock' else M.P(*parts)


def wait_meas(struct):
    return ('C1', 'M', 'S') if struct == 'mock' else ()


def out_parents(struct):
    return ('R2', 'A06') if struct == 'mock' else ()


def kfs_of(seg, struct, me):
    kf = {k: me['k' + k] for k in TWO}
    if struct == 'mock':
        kf['Q0'] = me['kQ0']
    else:
        for k in ('Q0', 'C1', 'S', 'M'):
            kf[k] = seg.meas_kf(k)
    return kf


def mem_gate_of(struct):
    if struct == 'mock':
        return None
    import e6m_stage0_S_engine as EN
    return EN.source_mem_gate


def mem_gate_s_of(struct):
    """断点续跑记忆门（附属第 7 项连续链）：mock = 转录 e6m_s_ops.src_mem_gate_s；真实 = 源 e6l_ops.mem_gate（state / d0 / d1 原样透传）。"""
    if struct == 'mock':
        import e6m_s_ops as SO
        return SO.src_mem_gate_s
    return source_mem_gate_s


def source_mem_gate_s(st, sc, U, kind, b, state=None, d0=0, d1=None):
    """源 e6l_ops.mem_gate 包成 e6m_s_ops.Ctx(mem_gate_s=…) 的接口：→ (G (P, len(ids)), 末状态)。"""
    import e6l_ops as LO
    op = {'HG': 'HG%d', 'LAG1': 'LAG1_%d'}[kind] % int(b)
    G, stt, _ = LO.mem_gate(st, sc, U, LO.parse_op(op), b_day=np.full(st.seg.T, float(b)), state=state, d0=d0, d1=d1)
    return G, stt


def struct_attr(st, name):
    """mock 结构把源结构字段（drop / base / legs）放在自身；真实 Struct 放在 st.st。"""
    return getattr(st, name) if hasattr(st, name) else getattr(st.st, name)


def env_struct():
    return os.environ.get('E6M_STRUCT', 'mock')
