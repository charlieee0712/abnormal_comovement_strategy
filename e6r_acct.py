# -*- coding: utf-8 -*-
"""E6r 账户运行器（e6r_engine.step 的 Python 端；沿 e6q_acct）：市场输入（E6r 缓存：E6q 面板 / 源名单 / 触发硬链 + 本轮 UNION_LEVEL_T8 / cvr20 / cvr5 / seckey /
DEV .015 形成权重）、形成名单 CSR、形成层算子数组（overlay/<form>|<mem>.npz，与 CSR 逐项对齐）、状态分配（批次 18 列 / 标签 6 列 / 成交日志 11 + 8 列）、
分段运行与 checkpoint（严格恢复校验：数量、待卖、REARM 词表与观察来源、标签余额、state / 代码 hash）。
registry 行 → 引擎参数（spec_params）：weight_scheme → 算子模式与 cap 参数；exit_op → M3 / M4 / GATE_REARM 开关与 A_ref；trigger → 面板或 T1A_TIME_LEVEL_RANK 选择模式。"""
import os
import json
import hashlib

import numpy as np

import e6r_core as O
import e6r_engine as E

TKCAP = 1 << 15
PBCAP = 1 << 13
RT_NODES = 20000                 # 入场 TICKETS / JOINT 首个可行映射的节点上限（E6q 20 万 → 2 万：S0-K 实测 76 条路径 29 万抽样，可行实例需 2–20 万节点的只占 0.024%，触限实例占计算量 78%；notes §8）
RT_VER = 0                     # 入场票据求解器：0 = rt_match（E6q 同一回溯 + 四条必要条件剪枝，生产）；1 = rt_match2（字典序贪心 + 见证，开发期试验：同解但触限更多，未采用，见 notes）；2 = 两版比对


TL_LAB_NONE = -9


def reset_tl_labels(TL_i, TL_f, n):
    """成交日志标签列（TL_i 8–11 = cohort / 算子标签 / CVR20 标签 / T0 状态，TL_f 6–7 = 形成 / 计划账户权重）置哨兵：引擎只在有标签的成交行写这些列，
    缓冲区分块落盘后复用，不重置会让无标签行（部分额外批次 / 部署买入）带上一块的残留值。哨兵导出为空。"""
    if TL_i.shape[1] > 11:
        TL_i[:n, 8] = -1
        TL_i[:n, 9:12] = TL_LAB_NONE
    if TL_f.shape[1] > 7:
        TL_f[:n, 6:8] = np.nan


def _arr_sha(d):
    """附加数组字典的 sha256（键排序；形状 + 字节）。"""
    h = hashlib.sha256()
    for k in sorted(d):
        a = np.ascontiguousarray(d[k])
        h.update(k.encode())
        h.update(str(a.shape).encode())
        h.update(str(a.dtype).encode())
        h.update(a.tobytes())
    return h.hexdigest()


_ENGINE_SHA = []


def engine_sha():
    """引擎文件 sha256（进程内缓存；checkpoint 版本校验用）。"""
    if not _ENGINE_SHA:
        _ENGINE_SHA.append(O.sha_file(E.__file__))
    return _ENGINE_SHA[0]


def lcap_for(H):
    return 1 << 15 if H <= 5 else (1 << 16 if H <= 10 else (1 << 17 if H <= 20 else (1 << 18 if H <= 30 else 1 << 19)))


def incap_for(H):
    return 1 << 20 if H <= 10 else (1 << 21 if H <= 20 else 1 << 22)


class Market(object):
    """全程市场输入（只读 mmap）+ 形成名单 CSR + 形成层算子数组。"""

    def __init__(self, cd=None):
        cd = cd or O.cache_dir()
        self.cd = cd
        pdir = os.path.join(cd, 'panels')
        tdir = os.path.join(cd, 'triggers')
        L = lambda k, d=pdir: np.load(os.path.join(d, k + '.npy'), mmap_mode='r')
        self.dates = np.load(os.path.join(pdir, 'dates.npy'))
        self.codes = np.load(os.path.join(pdir, 'codes.npy'))
        self.T, self.N = len(self.dates), len(self.codes)
        self.pv = L('pv_ff')
        self.pc = L('pc_ff')
        self.pcobs = L('pc')
        self.cvr = L('cvr1d')
        self.cpct = L('cvr_pct')
        self.sellable = L('sellable')
        self.buyable = L('buyable')
        self.isopen = L('is_open')
        self.sig20 = L('sig20')
        self.adv20 = L('adv20')
        self.zsz = L('zsize')
        self.ind = L('ind')
        self.pvage = L('pv_age')
        self.bench = np.asarray(L('bench'))
        self.capsh = np.ascontiguousarray(np.asarray(L('ind_share')))
        self.nclean = np.ascontiguousarray(np.asarray(L('nclean'), dtype=np.float64))
        self.cvr20 = L('cvr20')
        self.cvr5 = np.load(os.path.join(cd, 'e6r_cvr5', 'cvr5.npy'), mmap_mode='r')
        self.seckey = np.ascontiguousarray(np.asarray(L('seckey'), dtype=np.int64))
        self.trig_dir = tdir
        self.t1a = L('T1a', tdir)
        self.lvl = L('T1b_LEVEL', tdir)
        self._trig = {}
        self.iskid = L('iskid')
        self.n_isk = int(np.asarray(self.ind).max() + 1) * 3
        self.zero_trig = np.load(os.path.join(tdir, 'NONE.npy'), mmap_mode='r')
        self.di = {d: i for i, d in enumerate(self.dates)}
        self.cj = {c: j for j, c in enumerate(self.codes)}
        self._src = {}
        self._src15 = {}
        self._fm = {}
        self._ov = {}
        self.nan_expo = np.full(self.T, np.nan)

    def trig(self, name):
        if name not in self._trig:
            self._trig[name] = np.load(os.path.join(self.trig_dir, name + '.npy'), mmap_mode='r')
        return self._trig[name]

    def source(self, seg):
        if seg not in self._src:
            self._src[seg] = np.load(os.path.join(self.cd, 'source', '%s.npz' % seg), allow_pickle=False)
        return self._src[seg]

    def source15(self, seg):
        if seg not in self._src15:
            self._src15[seg] = np.load(os.path.join(self.cd, 'source15', '%s.npz' % seg), allow_pickle=False)
        return self._src15[seg]

    def formation(self, form, mem, w15=False):
        """全程形成名单 CSR（f_ptr、f_col、f_w）：四段源名单拼接（与 e6q_acct.Market.formation 同式）；w15 = DEV .015 权重（同名单、同序）。"""
        k = (form, mem, bool(w15))
        if k in self._fm:
            return self._fm[k]
        ts, cs, ws = [], [], []
        for s in O.SEGS:
            z = self.source(s)
            dd = np.array([self.di[d] for d in z['dates']])
            cc = np.array([self.cj[c] for c in z['codes']])
            ts.append(dd[z['fm_t|%s|%s' % (form, mem)]])
            cs.append(cc[z['fm_c|%s|%s' % (form, mem)]])
            ws.append(self.source15(s)['fm_w15|%s|%s' % (form, mem)] if w15 else z['fm_w|%s|%s' % (form, mem)])
        t = np.concatenate(ts)
        c = np.concatenate(cs)
        w = np.concatenate(ws)
        o = np.lexsort((c, t))
        t, c, w = t[o], c[o], w[o]
        ptr = np.searchsorted(t, np.arange(self.T + 1)).astype(np.int64)
        self._fm[k] = (ptr, c.astype(np.int64), w.astype(np.float64))
        return self._fm[k]

    def overlay(self, form, mem):
        """形成层算子数组（e6r_overlay 产物，与 formation(form, mem) 的 CSR 逐项对齐）。"""
        k = (form, mem)
        if k not in self._ov:
            z = np.load(os.path.join(self.cd, 'overlay', '%s|%s.npz' % (form, mem)), allow_pickle=False)
            self._ov[k] = {n: z[n] for n in z.files}
        return self._ov[k]


EXIT_MAP = {
    # exit_op: (m3, half, rearm, gate_rearm, A_ref)
    'NATIVE': (0, 0, 0, 0, 0.0),
    'EXIT_GATE_LIQ_1E8': (1, 0, 0, 0, 1e8),
    'EXIT_GATE_LIQ_5E8': (1, 0, 0, 0, 5e8),
    'EXIT_HALF_REARM': (0, 1, 1, 0, 0.0),
    'GATE_REARM_1E8': (1, 1, 1, 1, 1e8),
    'GATE_REARM_5E8': (1, 1, 1, 1, 5e8),
}
TRIG_PANEL = {'NONE': None, 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE', 'UNION_T1a_T8': 'UNION_T1a_T8',
              'UNION_LEVEL_T8': 'UNION_LEVEL_T8', 'T1A_TIME_LEVEL_RANK': 'T1a'}
SCHEME_MODE = {'FLAT': E.OV_NONE, 'GATE_STATE': E.OV_GATE, 'DROP_T3': E.OV_GATE, 'TILT_CVR_L050': E.OV_TILT, 'TILT_CVR_L025': E.OV_TILT,
               'TILT_SIZE_L050': E.OV_TILT, 'TILT_CVR5_L050': E.OV_TILT, 'GATE_TILT': E.OV_GATETILT, 'TILT_CVR_CELL_L050': E.OV_CELL,
               'TILT_H': E.OV_TILTH, 'UNIFORM_CAP15': E.OV_NONE}
SCHEME_LABEL = {'GATE_STATE': 'lab20', 'DROP_T3': 'lab20', 'TILT_CVR_L050': 'lab20', 'TILT_CVR_L025': 'lab20', 'GATE_TILT': 'lab20', 'TILT_H': 'lab20',
                'TILT_SIZE_L050': 'labsz', 'TILT_CVR5_L050': 'lab5', 'TILT_CVR_CELL_L050': 'labcell', 'FLAT': 'lab20', 'UNIFORM_CAP15': 'lab20'}


def _flag(v):
    if isinstance(v, (bool, np.bool_)):
        return bool(v)
    return str(v).strip().lower() == 'true'


class Account(object):
    """一个账户（一条执行对象、一条随机路径、一条影子或反馈路径）的状态与运行。"""

    def __init__(self, mk, ip, fp, trig_name, f_csr, ov=None, targets=None, lcap=None, incap=None, tlcap=0, start=0):
        self.mk = mk
        T, N = mk.T, mk.N
        self.ip = np.asarray(ip, np.int64)
        self.fp = np.asarray(fp, np.float64)
        H = int(self.ip[E.IP_H])
        Hmax = max(H, 30) if int(self.ip[E.IP_OVL]) == E.OV_TILTH or int(self.ip[E.IP_ERND]) == E.ER_TENOR else H
        lcap = lcap or lcap_for(Hmax)
        incap = incap or incap_for(Hmax)
        self.trig = mk.trig(trig_name) if trig_name else mk.zero_trig
        self.f_ptr, self.f_col, self.f_w = f_csr
        nf = len(self.f_w)
        ov = ov or {}
        z1 = lambda dt: np.zeros(max(nf, 1), dt)
        self.ov_rho = np.ascontiguousarray(ov.get('rho', np.ones(max(nf, 1))), dtype=np.float64)
        self.ov_lab = np.ascontiguousarray(ov.get('lab', z1(np.int8)), dtype=np.int8)
        self.ov_lab20 = np.ascontiguousarray(ov.get('lab20', z1(np.int8)), dtype=np.int8)
        self.ov_st = np.ascontiguousarray(ov.get('st0', np.full(max(nf, 1), -1, np.int8)), dtype=np.int8)
        self.ov_cell = np.ascontiguousarray(ov.get('cell', np.full(max(nf, 1), -1, np.int32)), dtype=np.int32)
        self.ov_pin = np.ascontiguousarray(ov.get('pin', z1(np.bool_)), dtype=np.bool_)
        for nm in ('ov_rho', 'ov_lab', 'ov_lab20', 'ov_st', 'ov_cell', 'ov_pin'):
            if len(getattr(self, nm)) < nf:
                raise RuntimeError('形成层数组 %s 长度 %d < 名单 %d' % (nm, len(getattr(self, nm)), nf))
        self.nf_ptr, self.nf_col = np.zeros(T + 1, np.int64), np.zeros(0, np.int64)
        self.u_ptr, self.u_col = np.zeros(T + 1, np.int64), np.zeros(0, np.int64)
        self.n_ptr, self.n_col = np.zeros(T + 1, np.int64), np.zeros(0, np.int64)
        NL = int(self.ip[E.IP_NLAYER])
        tg = targets or {}
        self.tg_amt = np.zeros((1, 1))
        self.tg_cnt = np.zeros((1, 1), np.int64)
        self.tg_isk = np.zeros((1, 1), np.int64)
        self.tg_re = np.zeros((1, 4))
        self.p_bern = np.ascontiguousarray(tg.get('bern', np.zeros((T, NL))), dtype=np.float64)
        self.tg_cancel = np.zeros(T)
        tlr = int(self.ip[E.IP_SEL]) == E.SM_TLR
        self.tg_b = np.ascontiguousarray(tg.get('b', np.zeros((T, E.NB)) if tlr else np.zeros((T, E.NB))), dtype=np.float64)
        self.tg_isk2 = np.ascontiguousarray(tg.get('isk2', np.zeros((T, mk.n_isk * E.NB))), dtype=np.float64)
        self.tg_aisk = np.ascontiguousarray(tg.get('aisk', np.zeros((T, mk.n_isk * E.NB))), dtype=np.float64)
        self.tg_rchk = np.zeros(T)
        self.tgt_expo = np.ascontiguousarray(mk.nan_expo, dtype=np.float64)
        self.L_i = np.zeros((lcap, E.NLI), np.int64)
        self.L_f = np.zeros((lcap, E.NLF), np.float64)
        self.L_id = np.zeros(lcap, np.int64)
        self.q = np.zeros(N)
        self.ep_until = np.full(N, -1, np.int64)
        self.ep_clear = np.zeros(N, np.int64)
        self.last_exit_due = np.full(N, -1, np.int64)
        self.first_held = np.full(N, -1, np.int64)
        self.TK_f = np.zeros(TKCAP)
        self.TK_i = np.zeros((TKCAP, E.NTKI), np.int64)
        self.LK_f = np.zeros(TKCAP)
        self.LK_i = np.zeros((TKCAP, E.NTKI), np.int64)
        self.PB_i = np.zeros((PBCAP, E.NPBI), np.int64)
        self.PB_f = np.zeros(PBCAP)
        self.PL_i = np.zeros((N, E.NPLI), np.int64)          # 次日成交批次的形成标签（逐证券；计划日写、成交日读）
        self.PL_f = np.zeros((N, E.NPLF), np.float64)
        self.S_f = np.zeros(E.NSF)
        self.S_i = np.zeros(E.NSI, np.int64)
        V0 = float(self.fp[E.FP_V0])
        self.S_f[E.SF_CASH] = V0
        self.S_f[E.SF_VPREV] = V0
        self.IN_i = np.zeros((incap, E.NIN_I), np.int64)
        self.IN_f = np.zeros((incap, 2), np.float64)
        self.DY = np.zeros((T, E.NDY))
        self.HOLDH = np.zeros(64, np.int64)
        self.LOTH = np.zeros(256, np.int64)
        self.RISK = np.zeros((T, max(NL, 1)), np.int64)
        self.HITS = np.zeros((T, max(NL, 1)), np.int64)
        self.TL_i = np.zeros((max(tlcap, 1), E.NTLI), np.int64)
        self.TL_f = np.zeros((max(tlcap, 1), E.NTLF), np.float64)
        reset_tl_labels(self.TL_i, self.TL_f, len(self.TL_i))
        self.DBG = np.zeros(1)
        self.next_day = start

    def run(self, d0, d1):
        if d0 != self.next_day:
            raise RuntimeError('续跑日不连续：%d vs %d' % (d0, self.next_day))
        mk = self.mk
        E.step(d0, d1, self.ip, self.fp, mk.pv, mk.pc, mk.pcobs, mk.cvr, mk.cpct, self.trig, mk.t1a, mk.lvl, mk.sellable, mk.buyable, mk.isopen,
               mk.sig20, mk.adv20, mk.zsz, mk.ind, mk.capsh, mk.bench, mk.pvage, mk.iskid, mk.nclean, self.tgt_expo,
               self.f_ptr, self.f_col, self.f_w, self.u_ptr, self.u_col, self.n_ptr, self.n_col, self.nf_ptr, self.nf_col,
               self.tg_amt, self.tg_cnt, self.tg_isk, self.tg_re, self.p_bern, self.tg_cancel, self.tg_b, self.tg_isk2, self.tg_aisk, self.tg_rchk,
               self.L_i, self.L_f, self.L_id, self.q, self.ep_until, self.ep_clear, self.last_exit_due, self.first_held,
               self.TK_f, self.TK_i, self.LK_f, self.LK_i, self.PB_i, self.PB_f, self.S_f, self.S_i, self.IN_i, self.IN_f, self.DY, self.HOLDH,
               self.LOTH, self.RISK, self.HITS, self.TL_i, self.TL_f, self.DBG,
               self.ov_rho, self.ov_lab, self.ov_lab20, self.ov_st, self.ov_cell, self.ov_pin, mk.seckey, self.PL_i, self.PL_f)
        self.next_day = d1
        if self.S_i[E.SI_ERR] != 0:
            raise RuntimeError('引擎错误码 %d（%s）' % (self.S_i[E.SI_ERR], {1: '批次容量', 2: '标签容量', 3: '非法标签', 4: 'ORIGINAL_DUE 双花',
                                                                         5: '常规缺口标签不足', 6: '额外买入标签不足', 7: '现金为负',
                                                                         8: '意向日志容量', 9: '现金不足以付强制卖出与费用', 10: '早退腿容量',
                                                                         11: '成交日志容量', 13: '两层投影失败', 14: '随机票据容量'}.get(int(self.S_i[E.SI_ERR]), '?')))
        return self

    STATE = ('L_i', 'L_f', 'L_id', 'q', 'ep_until', 'ep_clear', 'last_exit_due', 'first_held', 'TK_f', 'TK_i', 'LK_f', 'LK_i', 'PB_i', 'PB_f', 'PL_i', 'PL_f',
             'S_f', 'S_i', 'IN_i', 'IN_f', 'DY', 'HOLDH', 'LOTH', 'RISK', 'HITS')
    USED = {'L_i': E.SI_NL, 'L_f': E.SI_NL, 'L_id': E.SI_NL, 'TK_f': E.SI_NTK, 'TK_i': E.SI_NTK, 'LK_f': E.SI_NLK, 'LK_i': E.SI_NLK,
            'PB_i': E.SI_NPB, 'PB_f': E.SI_NPB, 'IN_i': E.SI_NIN, 'IN_f': E.SI_NIN}

    def _used(self, k):
        a = getattr(self, k)
        return a[:int(self.S_i[self.USED[k]])] if k in self.USED else a

    def state_hash(self, keys=None):
        h = hashlib.sha256()
        for k in (self.STATE if keys is None else keys):
            a = np.ascontiguousarray(self._used(k))
            h.update(k.encode())
            h.update(str(a.shape).encode())
            h.update(a.tobytes())
        h.update(str(self.next_day).encode())
        return h.hexdigest()

    def validate_state(self):
        """plan §6.5：数量有限非负；0 ≤ 待卖 ≤ 余量；M4 / GATE_REARM 半量状态在词表内（0 / 1 / 2）；has_cleared ∈ {0, 1}；
        待卖 > 0 的 M3 / GATE_REARM 请求必有 deadline ≤ due；HALF / FULL 有观察来源（first_decision ≥ 0）；标签未消费余额 ≤ 现金。"""
        n = int(self.S_i[E.SI_NL])
        Lf = self.L_f[:n]
        Li = self.L_i[:n]
        alive = Li[:, 7] == 1
        if not np.isfinite(Lf[alive, 0]).all() or (Lf[alive, 0] < -1e-12).any():
            raise RuntimeError('checkpoint 批次数量非有限或为负')
        tgt = Lf[alive, 4]
        if not np.isfinite(tgt).all() or (tgt < -1e-12).any() or (tgt > Lf[alive, 0] * (1 + 1e-9) + 1e-9).any():
            raise RuntimeError('checkpoint 当日待售量非有限 / 为负 / 大于剩余量')
        pend = Lf[alive, 5]
        if not np.isfinite(pend).all() or (pend < -1e-12).any() or (pend > Lf[alive, 0] * (1 + 1e-9) + 1e-9).any():
            raise RuntimeError('checkpoint 请求待关闭量非有限 / 为负 / 大于剩余量')
        ph = Li[alive, 10]
        if not np.isin(ph, (0, 1, 2)).all():
            raise RuntimeError('checkpoint 半量 / REARM 状态不在词表内')
        if not np.isin(Li[alive, 11], (0, 1)).all():
            raise RuntimeError('checkpoint has_cleared 非 0 / 1')
        if int(self.ip[E.IP_GR]) == 1:
            early = alive & (Li[:, 3] == E.LQ_EARLY)
            pe = early & (Lf[:, 5] > 1e-12 * np.maximum(1.0, Lf[:, 0]))
            if (pe & ((Li[:, 9] < 0) | (Li[:, 9] > Li[:, 2]))).any():
                raise RuntimeError('checkpoint 待卖请求缺 deadline 或 deadline 晚于原 due')
            if ((ph > 0) & (Li[alive, 8] < 0)).any():
                raise RuntimeError('checkpoint HALF / FULL 请求缺观察来源')
        nt = int(self.S_i[E.SI_NTK])
        tk = self.TK_f[:nt][self.TK_i[:nt, 2] == 1]
        if not np.isfinite(tk).all() or (tk < -1e-9).any():
            raise RuntimeError('checkpoint 标签金额非法')
        if tk.sum() > self.S_f[E.SF_CASH] * (1 + 1e-9) + 1e-6:
            raise RuntimeError('checkpoint 标签余额大于现金')

    def checkpoint(self, path, meta, skip=(), compress=False, extra=None):
        """原子 checkpoint；skip = 不存的纯输出数组（随机路径 A2 末状态不存 DY：引擎从不回读已过日的 DY 行，推导段读数随 meta 携带），
        compress = 压缩写（随机路径）；extra = 附加数组（稀疏意向行），另记 sha；state_sha256 只覆盖实存的 STATE 数组。"""
        self.validate_state()
        keys = [k for k in self.STATE if k not in skip]
        arr = {k: self._used(k) for k in keys}
        arr['next_day'] = np.array([self.next_day])
        m = dict(meta, state_sha256=self.state_hash(keys), code_sha256=engine_sha(), skipped=list(skip))
        if extra:
            arr.update(extra)
            m['extra_sha256'] = _arr_sha(extra)
        arr['meta'] = np.array([json.dumps(m, sort_keys=True)])
        (O.atomic_write_npz_c if compress else O.atomic_write_npz)(path, **arr)

    def checkpoint_compact(self, path, meta):
        """随机路径 A2 末状态（紧凑）：先 compact_lots（引擎原函数：只删已关闭批次、保序、同步意向的批次引用），意向表只存仍被在册批次引用的行
        （原行号；其余意向行是纯输出，推导段计数随 meta 的 A2 读数携带），不存 DY；压缩写。续跑 = 一次跑完由 B 相每个引用的 0 号路径逐位核验（ck_equal）。"""
        E.compact_lots(self.L_i, self.L_f, self.L_id, self.IN_i, self.S_i)
        nl = int(self.S_i[E.SI_NL])
        ref = self.L_i[:nl, 6]
        idx = np.unique(ref[ref >= 0]).astype(np.int64)
        self.checkpoint(path, dict(meta, in_sparse=True), skip=('DY', 'IN_i', 'IN_f'), compress=True,
                        extra=dict(IN_idx=idx, IN_isel=self.IN_i[idx].copy(), IN_fsel=self.IN_f[idx].copy()))

    def restore(self, path, expect_code=True):
        z = np.load(path, allow_pickle=False)
        meta = json.loads(str(z['meta'][0]))
        if expect_code and meta.get('code_sha256') != engine_sha():
            raise RuntimeError('checkpoint 代码版本不符')
        keys = [k for k in self.STATE if k not in set(meta.get('skipped', []))]
        for k in keys:
            a = getattr(self, k)
            v = z[k]
            if v.dtype != a.dtype:
                raise RuntimeError('checkpoint 类型不符：%s %s ≠ %s' % (k, v.dtype, a.dtype))
            if k in self.USED:
                if len(v) > len(a) or v.shape[1:] != a.shape[1:]:
                    raise RuntimeError('checkpoint 容量不符：%s' % k)
                a[:len(v)] = v
            else:
                if a.shape != v.shape:
                    raise RuntimeError('checkpoint 形状不符：%s' % k)
                a[...] = v
        self.next_day = int(z['next_day'][0])
        if self.state_hash(keys) != meta['state_sha256']:
            raise RuntimeError('checkpoint 状态 hash 不符')
        if 'extra_sha256' in meta:
            ex = {k: z[k] for k in ('IN_idx', 'IN_isel', 'IN_fsel') if k in z.files}
            if _arr_sha(ex) != meta['extra_sha256']:
                raise RuntimeError('checkpoint 附加数组 hash 不符')
        if meta.get('in_sparse'):
            idx = z['IN_idx']
            n_in = int(self.S_i[E.SI_NIN])
            if len(idx) and (idx.min() < 0 or idx.max() >= n_in or n_in > len(self.IN_i)):
                raise RuntimeError('checkpoint 稀疏意向行越界')
            self.IN_i[idx] = z['IN_isel']
            self.IN_f[idx] = z['IN_fsel']
        self.validate_state()
        return meta


def ip_fp(H, trig_mode, sel=E.SM_REAL, exit_on=False, ideal=False, seed=0, shadow=False, tlog=False, feedback=None, m3=0, half=0, rearm=0, gr=0,
          aref=0.0, pstar=None, theta=None, qdays=None, fhit=0, ovl=E.OV_NONE, ernd=E.ER_NONE, lam=0.0, scap=None, nodes=RT_NODES, rtv=RT_VER):
    ip = np.zeros(E.NIP, np.int64)
    ip[E.IP_TLOG] = 1 if tlog else 0
    ip[E.IP_H] = H
    ip[E.IP_TRIG] = trig_mode
    ip[E.IP_SEL] = sel
    ip[E.IP_FUND] = E.FD_NATIVE
    ip[E.IP_LAG] = 1
    ip[E.IP_MAT] = 0
    ip[E.IP_RE] = E.RE_ALLOW
    ip[E.IP_GUARD] = E.GD_OFF
    ip[E.IP_EXIT] = 1 if exit_on else 0
    ip[E.IP_IDEAL] = 1 if ideal else 0
    ip[E.IP_RECON] = E.RC_NONE
    ip[E.IP_SEED] = seed & ((1 << 62) - 1)
    ip[E.IP_SHADOW] = 1 if shadow else 0
    ip[E.IP_NLAYER] = max(H, 30) if ovl == E.OV_TILTH or ernd == E.ER_TENOR else H
    ip[E.IP_DEPLOY] = E.DP_NONE
    ip[E.IP_CAP] = E.CP_SOURCE
    ip[E.IP_RENEW] = 0
    ip[E.IP_RECYCLE] = E.RY_NONE
    ip[E.IP_FEEDBACK] = 1 if feedback else 0
    ip[E.IP_M1] = 0
    ip[E.IP_M2] = 0
    ip[E.IP_M3] = m3
    ip[E.IP_HALF] = half
    ip[E.IP_REARM] = rearm
    ip[E.IP_QDAYS] = O.QUEUE_DAYS if qdays is None else qdays
    ip[E.IP_ROUTE] = 0
    ip[E.IP_RT] = E.RT_NONE
    ip[E.IP_FIRSTHIT] = fhit
    ip[E.IP_NODES] = nodes
    ip[E.IP_OVL] = ovl
    ip[E.IP_ERND] = ernd
    ip[E.IP_GR] = gr
    ip[E.IP_RTV] = rtv
    fp = np.zeros(E.NFP)
    fp[E.FP_V0] = O.V0
    fp[E.FP_FEE] = O.FEE_RATE
    fp[E.FP_SCAP] = O.STOCK_CAP if scap is None else scap
    fp[E.FP_IDEV] = O.IND_DEV
    fp[E.FP_ETA] = 0.5
    fp[E.FP_RA] = 1e8
    fp[E.FP_RK] = 0.5
    fp[E.FP_RD] = 0.5
    fp[E.FP_P0] = O.P0_PIVOT
    fp[E.FP_PSTAR] = O.P_STAR if pstar is None else pstar
    fp[E.FP_AREF] = aref
    fp[E.FP_THETA] = O.THETA if theta is None else theta
    fp[E.FP_LAMBDA] = lam
    fp[E.FP_RCAP] = O.RESEARCH_CAP
    if feedback:
        fp[E.FP_FBA], fp[E.FP_FBK], fp[E.FP_FBD] = feedback
    return ip, fp


def spec_params(row, sel=E.SM_REAL, seed=0, shadow=False, tlog=False, feedback=None, fhit=0, pstar=None, theta=None, ernd=E.ER_NONE, force_lambda=None, rtv=None):
    """registry 行（dict：form / memory / funding_H / trigger / weight_scheme / exit_op / scenario / cap_single_parameter / lambda_weight）→ (ip, fp, trig_name)。
    trigger = NONE 的非 NATIVE 退出算子 = 零干预端点（无意向，与 NATIVE 同路径）；T1A_TIME_LEVEL_RANK = 本账户 T1a 合法意向额 × 当前 LEVEL 坏度排序选择。
    force_lambda 只供 S0-F LAMBDA0 恒等（λ = 0 → 直接走源 FLAT 分配）。"""
    H = int(float(row['funding_H']))
    trig = row['trigger']
    scheme = row['weight_scheme']
    m3, hf, ra, gr, aref = EXIT_MAP[row['exit_op']]
    act = trig != 'NONE'
    lam = float(row.get('lambda_weight') or 0.0) if force_lambda is None else float(force_lambda)
    scap = float(row.get('cap_single_parameter') or O.STOCK_CAP)
    ovl = SCHEME_MODE[scheme]
    if ovl in (E.OV_TILT, E.OV_CELL) and lam == 0.0:
        ovl, scap = E.OV_NONE, O.STOCK_CAP                  # plan §4.4：λ = 0 直接调用源 FLAT 分配（零干预分派）
    s = sel
    if trig == 'T1A_TIME_LEVEL_RANK' and sel == E.SM_REAL:
        s = E.SM_TLR
    ip, fp = ip_fp(H, E.TM_PANEL if act else E.TM_NONE, sel=s, exit_on=act and not shadow, ideal=row['scenario'] == O.IDEAL, seed=seed,
                   shadow=shadow, tlog=tlog, feedback=feedback, m3=m3, half=hf, rearm=ra, gr=gr, aref=aref, pstar=pstar, theta=theta, fhit=fhit,
                   ovl=ovl, ernd=ernd, lam=lam, scap=scap, rtv=RT_VER if rtv is None else rtv)
    return ip, fp, TRIG_PANEL[trig]


def overlay_arrays(mk, row):
    """registry 行 → 引擎形成层数组（rho / lab / lab20 / st0 / cell / pin）；FLAT / UNIFORM 只带日志用的 lab20 / st0 / cell。"""
    z = mk.overlay(row['form'], row['memory'])
    scheme = row['weight_scheme']
    ov = dict(lab20=z['lab20'], st0=z['st0'], cell=z['cell'])
    lab = SCHEME_LABEL.get(scheme, 'lab20')
    ov['lab'] = z[lab]
    if scheme in ('FLAT', 'UNIFORM_CAP15', 'TILT_H'):
        ov['rho'] = np.ones(len(z['lab20']))
        ov['pin'] = z['lab20'] == 0
    else:
        ov['rho'] = z['rho|' + scheme]
        ov['pin'] = z['pin|' + scheme]
    return ov
