# -*- coding: utf-8 -*-
"""E6o 账户运行器（e6o_engine.step 的 Python 端）：市场输入（mmap 共享，只读）、形成名单 CSR、状态分配、分段运行与 checkpoint。
一个 Market 对象在进程内加载一次；Account.run(d0, d1) 可分段续跑；checkpoint 保存全部状态数组与代码 / 合同 hash（plan §14.2）。"""
import os
import json
import hashlib

import numpy as np

import e6o_core as O
import e6o_engine as E

LCAP = 1 << 15
TKCAP = 1 << 14
PBCAP = 1 << 12
INCAP = 1 << 20


class Market(object):
    """全程市场输入（只读 mmap）+ 形成名单 / 自然门 / NEXT 序 CSR。"""

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
        sh = np.asarray(L('ind_share'))
        self.capsh = np.ascontiguousarray(sh)
        self.trig_dir = tdir
        self.t1a = L('T1a', tdir)
        self.lvl = L('T1b_LEVEL', tdir)
        self._trig = {}
        pk = os.path.join(pdir, 'iskid.npy')
        if not os.path.exists(pk):
            z = np.asarray(self.zsz)
            zz = np.where(np.isfinite(z), z, 0.0)
            ter = np.where(np.isfinite(z), np.clip(np.floor(zz * 3.0 - 1e-12), 0, 2), -1).astype(np.int64)
            indv = np.asarray(self.ind).astype(np.int64)
            isk = np.where((ter >= 0) & (indv >= 0), indv * 3 + ter, -1).astype(np.int32)
            tmp = pk + '.tmp%d.npy' % os.getpid()
            np.save(tmp, isk)
            os.replace(tmp, pk)
        self.iskid = L('iskid')
        self.n_isk = int(np.asarray(self.ind).max() + 1) * 3
        pz = os.path.join(tdir, 'NONE.npy')
        if not os.path.exists(pz):
            tmp = pz + '.tmp%d.npy' % os.getpid()
            np.save(tmp, np.zeros((self.T, self.N), np.int8))
            os.replace(tmp, pz)
        self.zero_trig = np.load(pz, mmap_mode='r')          # 与其它触发面板同类型（只读 mmap），免重复编译
        self.di = {d: i for i, d in enumerate(self.dates)}
        self.cj = {c: j for j, c in enumerate(self.codes)}
        self._src = {}

    def trig(self, name):
        if name not in self._trig:
            self._trig[name] = np.load(os.path.join(self.trig_dir, name + '.npy'), mmap_mode='r')
        return self._trig[name]

    def source(self, seg):
        if seg not in self._src:
            self._src[seg] = np.load(os.path.join(self.cd, 'source', '%s.npz' % seg), allow_pickle=False)
        return self._src[seg]

    def formation(self, form, mem):
        """全程形成名单 CSR（f_ptr、f_col、f_w）：四段源名单拼接（段内日 → 全程日；段 ccol → 全程列）。"""
        ts, cs, ws = [], [], []
        for s in O.SEGS:
            z = self.source(s)
            dd = np.array([self.di[d] for d in z['dates']])
            cc = np.array([self.cj[c] for c in z['codes']])
            t = dd[z['fm_t|%s|%s' % (form, mem)]]
            c = cc[z['fm_c|%s|%s' % (form, mem)]]
            ts.append(t)
            cs.append(c)
            ws.append(z['fm_w|%s|%s' % (form, mem)])
        t = np.concatenate(ts)
        c = np.concatenate(cs)
        w = np.concatenate(ws)
        o = np.lexsort((c, t))
        t, c, w = t[o], c[o], w[o]
        ptr = np.searchsorted(t, np.arange(self.T + 1)).astype(np.int64)
        return ptr, c.astype(np.int64), w.astype(np.float64)

    def gate_u(self, form):
        ts, cs = [], []
        for s in O.SEGS:
            z = self.source(s)
            dd = np.array([self.di[d] for d in z['dates']])
            cc = np.array([self.cj[c] for c in z['codes']])
            cells = z['gateU|%s' % form]
            ts.append(dd[z['cell_t'][cells]])
            cs.append(cc[z['cell_c'][cells]])
        t = np.concatenate(ts)
        c = np.concatenate(cs)
        o = np.lexsort((c, t))
        t, c = t[o], c[o]
        return np.searchsorted(t, np.arange(self.T + 1)).astype(np.int64), c.astype(np.int64)

    def next_order(self, mem):
        ts, cs, rs = [], [], []
        for s in O.SEGS:
            z = self.source(s)
            k = 'next_t|%s' % mem
            if k not in z.files:
                continue
            dd = np.array([self.di[d] for d in z['dates']])
            cc = np.array([self.cj[c] for c in z['codes']])
            ts.append(dd[z[k]])
            cs.append(cc[z['next_c|%s' % mem]])
            rs.append(z['next_r|%s' % mem])
        if not ts:
            return np.zeros(self.T + 1, np.int64), np.zeros(0, np.int64)
        t = np.concatenate(ts)
        c = np.concatenate(cs)
        r = np.concatenate(rs)
        o = np.lexsort((r, t))
        t, c = t[o], c[o]
        return np.searchsorted(t, np.arange(self.T + 1)).astype(np.int64), c.astype(np.int64)


EMPTY_CSR = (np.zeros(1, np.int64), np.zeros(0, np.int64))


class Account(object):
    """一个账户（一条执行对象或一条随机路径）的状态与运行。"""

    def __init__(self, mk, ip, fp, trig_name, f_csr, u_csr=None, n_csr=None, targets=None, V0=1e8, lcap=LCAP, incap=INCAP):
        self.mk = mk
        T, N = mk.T, mk.N
        self.ip = np.asarray(ip, np.int64)
        self.fp = np.asarray(fp, np.float64)
        self.trig = mk.trig(trig_name) if trig_name else mk.zero_trig
        self.f_ptr, self.f_col, self.f_w = f_csr
        self.u_ptr, self.u_col = u_csr if u_csr is not None else (np.zeros(T + 1, np.int64), np.zeros(0, np.int64))
        self.n_ptr, self.n_col = n_csr if n_csr is not None else (np.zeros(T + 1, np.int64), np.zeros(0, np.int64))
        NL = int(self.ip[E.IP_NLAYER])
        tg = targets or {}
        self.tg_amt = np.ascontiguousarray(tg.get('amt', np.zeros((T, max(NL, 4)))), dtype=np.float64)
        self.tg_cnt = np.ascontiguousarray(tg.get('cnt', np.zeros((T, NL), np.int64)), dtype=np.int64)
        self.tg_isk = np.ascontiguousarray(tg.get('isk', np.zeros((T, 1), np.int64)), dtype=np.int64)
        self.tg_re = np.ascontiguousarray(tg.get('re', np.zeros((T, 4))), dtype=np.float64)
        self.p_bern = np.ascontiguousarray(tg.get('bern', np.zeros((T, NL))), dtype=np.float64)
        self.tg_cancel = np.ascontiguousarray(tg.get('cancel', np.zeros(T)), dtype=np.float64)
        self.L_i = np.zeros((lcap, 8), np.int64)
        self.L_f = np.zeros((lcap, 4), np.float64)
        self.L_id = np.zeros(lcap, np.int64)
        self.q = np.zeros(N)
        self.ep_until = np.full(N, -1, np.int64)
        self.ep_clear = np.zeros(N, np.int64)
        self.last_exit_due = np.full(N, -1, np.int64)
        self.TK_f = np.zeros(TKCAP)
        self.TK_i = np.zeros((TKCAP, 4), np.int64)
        self.LK_f = np.zeros(TKCAP)
        self.LK_i = np.zeros((TKCAP, 4), np.int64)
        self.PB_i = np.zeros((PBCAP, 3), np.int64)
        self.PB_f = np.zeros(PBCAP)
        self.S_f = np.zeros(E.NSF)
        self.S_i = np.zeros(E.NSI, np.int64)
        self.S_f[E.SF_CASH] = V0
        self.S_f[E.SF_VPREV] = V0
        self.IN_i = np.zeros((incap, E.NIN_I), np.int64)
        self.IN_f = np.zeros((incap, 2), np.float64)
        self.DY = np.zeros((T, E.NDY))
        self.HOLDH = np.zeros(64, np.int64)
        self.RISK = np.zeros((T, max(NL, 1)), np.int64)
        tl = int(self.ip[E.IP_TLOG]) == 1
        self.TL_i = np.zeros((1 << 21 if tl else 1, 2), np.int64)
        self.TL_f = np.zeros((1 << 21 if tl else 1, 4), np.float64)
        self.next_day = 0

    def run(self, d0, d1):
        if d0 != self.next_day:
            raise RuntimeError('续跑日不连续：%d vs %d' % (d0, self.next_day))
        mk = self.mk
        E.step(d0, d1, self.ip, self.fp, mk.pv, mk.pc, mk.pcobs, mk.cvr, mk.cpct, self.trig, mk.t1a, mk.lvl, mk.sellable, mk.buyable, mk.isopen,
               mk.sig20, mk.adv20, mk.zsz, mk.ind, mk.capsh, mk.bench, mk.pvage, mk.iskid,
               self.f_ptr, self.f_col, self.f_w, self.u_ptr, self.u_col, self.n_ptr, self.n_col,
               self.tg_amt, self.tg_cnt, self.tg_isk, self.tg_re, self.p_bern, self.tg_cancel,
               self.L_i, self.L_f, self.L_id, self.q, self.ep_until, self.ep_clear, self.last_exit_due,
               self.TK_f, self.TK_i, self.LK_f, self.LK_i, self.PB_i, self.PB_f, self.S_f, self.S_i, self.IN_i, self.IN_f, self.DY, self.HOLDH, self.RISK,
               self.TL_i, self.TL_f)
        self.next_day = d1
        if self.S_i[E.SI_ERR] != 0:
            raise RuntimeError('引擎错误码 %d（%s）' % (self.S_i[E.SI_ERR], {1: '批次容量', 2: '标签容量', 3: '非法标签', 4: 'ORIGINAL_DUE 双花',
                                                                         5: '常规缺口标签不足', 6: '额外买入标签不足', 7: '现金为负',
                                                                         8: '意向日志容量', 9: '现金不足以付强制卖出与费用', 10: '早退腿容量',
                                                                         11: '成交日志容量'}.get(int(self.S_i[E.SI_ERR]), '?')))
        return self

    STATE = ('L_i', 'L_f', 'L_id', 'q', 'ep_until', 'ep_clear', 'last_exit_due', 'TK_f', 'TK_i', 'LK_f', 'LK_i', 'PB_i', 'PB_f', 'S_f', 'S_i',
             'IN_i', 'IN_f', 'DY', 'HOLDH', 'RISK')

    def state_hash(self):
        h = hashlib.sha256()
        for k in self.STATE:
            a = np.ascontiguousarray(getattr(self, k))
            h.update(k.encode())
            h.update(a.tobytes())
        h.update(str(self.next_day).encode())
        return h.hexdigest()

    def checkpoint(self, path, meta):
        n_in = int(self.S_i[E.SI_NIN])
        arr = {k: getattr(self, k) for k in self.STATE}
        arr['IN_i'] = self.IN_i[:max(n_in, 1)]
        arr['IN_f'] = self.IN_f[:max(n_in, 1)]
        arr['next_day'] = np.array([self.next_day])
        arr['meta'] = np.array([json.dumps(dict(meta, state_sha256=self.state_hash(), code_sha256=O.sha_file(E.__file__)), sort_keys=True)])
        O.atomic_write_npz(path, **arr)

    def restore(self, path, expect_code=True):
        z = np.load(path, allow_pickle=False)
        meta = json.loads(str(z['meta'][0]))
        if expect_code and meta.get('code_sha256') != O.sha_file(E.__file__):
            raise RuntimeError('checkpoint 代码版本不符')
        for k in self.STATE:
            a = getattr(self, k)
            v = z[k]
            if k in ('IN_i', 'IN_f'):
                a[:len(v)] = v
            else:
                if a.shape != v.shape:
                    raise RuntimeError('checkpoint 形状不符：%s' % k)
                a[...] = v
        self.next_day = int(z['next_day'][0])
        if self.state_hash() != meta['state_sha256']:
            raise RuntimeError('checkpoint 状态 hash 不符')
        return meta


def ip_fp(H, trig_mode, sel=E.SM_REAL, fund=E.FD_NONE, lag=1, maturity=0, reentry=E.RE_ALLOW, guard=E.GD_OFF, exit_on=False, ideal=False,
          recon=E.RC_NONE, seed=0, shadow=False, tlog=False):
    ip = np.zeros(E.NIP, np.int64)
    ip[E.IP_TLOG] = 1 if tlog else 0
    ip[E.IP_H] = H
    ip[E.IP_TRIG] = trig_mode
    ip[E.IP_SEL] = sel
    ip[E.IP_FUND] = fund
    ip[E.IP_LAG] = lag
    ip[E.IP_MAT] = maturity
    ip[E.IP_RE] = reentry
    ip[E.IP_GUARD] = guard
    ip[E.IP_EXIT] = 1 if exit_on else 0
    ip[E.IP_IDEAL] = 1 if ideal else 0
    ip[E.IP_RECON] = recon
    ip[E.IP_SEED] = seed & ((1 << 62) - 1)
    ip[E.IP_SHADOW] = 1 if shadow else 0
    ip[E.IP_NLAYER] = H
    fp = np.zeros(E.NFP)
    fp[E.FP_V0] = 1e8
    fp[E.FP_FEE] = O.FEE_RATE
    fp[E.FP_SCAP] = O.STOCK_CAP
    fp[E.FP_IDEV] = O.IND_DEV
    fp[E.FP_T2] = 0.01
    fp[E.FP_T6A] = 0.05
    fp[E.FP_T6B] = 2.0
    fp[E.FP_T1C] = 0.8
    fp[E.FP_T1D] = 0.9
    return ip, fp
