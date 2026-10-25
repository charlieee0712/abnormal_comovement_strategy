# -*- coding: utf-8 -*-
"""E6q 账户运行器（e6q_engine.step 的 Python 端；沿 e6p_acct）：市场输入（E6q 缓存：E6p 面板 / 源名单 / 触发硬链复用 + 本轮新面板）、
形成名单 CSR、状态分配（批次 14 列 / 标签 6 列 / 成交日志 8 + 6 列）、分段运行与 checkpoint（含请求 / 标签 first_denied / 半量 / REARM / 首达状态与代码 hash）。"""
import os
import json
import hashlib

import numpy as np

import e6q_core as O
import e6q_engine as E

TKCAP = 1 << 15
PBCAP = 1 << 13
RT_NODES = 200000


def lcap_for(H):
    return 1 << 15 if H <= 5 else (1 << 16 if H <= 10 else (1 << 17 if H <= 20 else 1 << 18))


def incap_for(H):
    return 1 << 20 if H <= 10 else (1 << 21 if H <= 20 else 1 << 22)


class Market(object):
    """全程市场输入（只读 mmap）+ 形成名单 CSR。"""

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
        self._fm = {}
        self.nan_expo = np.full(self.T, np.nan)

    def trig(self, name):
        if name not in self._trig:
            self._trig[name] = np.load(os.path.join(self.trig_dir, name + '.npy'), mmap_mode='r')
        return self._trig[name]

    def source(self, seg):
        if seg not in self._src:
            self._src[seg] = np.load(os.path.join(self.cd, 'source', '%s.npz' % seg), allow_pickle=False)
        return self._src[seg]

    def formation(self, form, mem):
        """全程形成名单 CSR（f_ptr、f_col、f_w）：四段源名单拼接（段内日 → 全程日；段 ccol → 全程列）。与 e6p_acct.Market.formation 同式。"""
        k = (form, mem)
        if k in self._fm:
            return self._fm[k]
        ts, cs, ws = [], [], []
        for s in O.SEGS:
            z = self.source(s)
            dd = np.array([self.di[d] for d in z['dates']])
            cc = np.array([self.cj[c] for c in z['codes']])
            ts.append(dd[z['fm_t|%s|%s' % (form, mem)]])
            cs.append(cc[z['fm_c|%s|%s' % (form, mem)]])
            ws.append(z['fm_w|%s|%s' % (form, mem)])
        t = np.concatenate(ts)
        c = np.concatenate(cs)
        w = np.concatenate(ws)
        o = np.lexsort((c, t))
        t, c, w = t[o], c[o], w[o]
        ptr = np.searchsorted(t, np.arange(self.T + 1)).astype(np.int64)
        self._fm[k] = (ptr, c.astype(np.int64), w.astype(np.float64))
        return self._fm[k]


class Account(object):
    """一个账户（一条执行对象、一条随机路径、一条影子或反馈路径）的状态与运行。"""

    def __init__(self, mk, ip, fp, trig_name, f_csr, targets=None, lcap=None, incap=None, tlcap=0, start=0):
        self.mk = mk
        T, N = mk.T, mk.N
        self.ip = np.asarray(ip, np.int64)
        self.fp = np.asarray(fp, np.float64)
        H = int(self.ip[E.IP_H])
        lcap = lcap or lcap_for(H)
        incap = incap or incap_for(H)
        self.trig = mk.trig(trig_name) if trig_name else mk.zero_trig
        self.f_ptr, self.f_col, self.f_w = f_csr
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
        self.tg_b = np.ascontiguousarray(tg.get('b', np.zeros((T, E.NB))), dtype=np.float64)
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
        self.PB_i = np.zeros((PBCAP, 3), np.int64)
        self.PB_f = np.zeros(PBCAP)
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
               self.LOTH, self.RISK, self.HITS, self.TL_i, self.TL_f, self.DBG)
        self.next_day = d1
        if self.S_i[E.SI_ERR] != 0:
            raise RuntimeError('引擎错误码 %d（%s）' % (self.S_i[E.SI_ERR], {1: '批次容量', 2: '标签容量', 3: '非法标签', 4: 'ORIGINAL_DUE 双花',
                                                                         5: '常规缺口标签不足', 6: '额外买入标签不足', 7: '现金为负',
                                                                         8: '意向日志容量', 9: '现金不足以付强制卖出与费用', 10: '早退腿容量',
                                                                         11: '成交日志容量'}.get(int(self.S_i[E.SI_ERR]), '?')))
        return self

    STATE = ('L_i', 'L_f', 'L_id', 'q', 'ep_until', 'ep_clear', 'last_exit_due', 'first_held', 'TK_f', 'TK_i', 'LK_f', 'LK_i', 'PB_i', 'PB_f', 'S_f', 'S_i',
             'IN_i', 'IN_f', 'DY', 'HOLDH', 'LOTH', 'RISK', 'HITS')
    USED = {'L_i': E.SI_NL, 'L_f': E.SI_NL, 'L_id': E.SI_NL, 'TK_f': E.SI_NTK, 'TK_i': E.SI_NTK, 'LK_f': E.SI_NLK, 'LK_i': E.SI_NLK,
            'PB_i': E.SI_NPB, 'PB_f': E.SI_NPB, 'IN_i': E.SI_NIN, 'IN_f': E.SI_NIN}

    def _used(self, k):
        a = getattr(self, k)
        return a[:int(self.S_i[self.USED[k]])] if k in self.USED else a

    def state_hash(self):
        h = hashlib.sha256()
        for k in self.STATE:
            a = np.ascontiguousarray(self._used(k))
            h.update(k.encode())
            h.update(str(a.shape).encode())
            h.update(a.tobytes())
        h.update(str(self.next_day).encode())
        return h.hexdigest()

    def validate_state(self):
        """plan §5.5：非有限、负待售量、待售量大于真实剩余量的状态不得恢复；标签未消费余额 ≤ 现金。"""
        n = int(self.S_i[E.SI_NL])
        Lf = self.L_f[:n]
        Li = self.L_i[:n]
        alive = Li[:, 7] == 1
        if not np.isfinite(Lf[alive, 0]).all() or (Lf[alive, 0] < -1e-12).any():
            raise RuntimeError('checkpoint 批次数量非有限或为负')
        tgt = Lf[alive, 4]
        if not np.isfinite(tgt).all() or (tgt < -1e-12).any() or (tgt > Lf[alive, 0] * (1 + 1e-9) + 1e-9).any():
            raise RuntimeError('checkpoint 待售量非有限 / 为负 / 大于剩余量')
        nt = int(self.S_i[E.SI_NTK])
        tk = self.TK_f[:nt][self.TK_i[:nt, 2] == 1]
        if not np.isfinite(tk).all() or (tk < -1e-9).any():
            raise RuntimeError('checkpoint 标签金额非法')
        if tk.sum() > self.S_f[E.SF_CASH] * (1 + 1e-9) + 1e-6:
            raise RuntimeError('checkpoint 标签余额大于现金')

    def checkpoint(self, path, meta):
        self.validate_state()
        arr = {k: self._used(k) for k in self.STATE}
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
            if k in self.USED:
                if len(v) > len(a) or v.shape[1:] != a.shape[1:]:
                    raise RuntimeError('checkpoint 容量不符：%s' % k)
                a[:len(v)] = v
            else:
                if a.shape != v.shape:
                    raise RuntimeError('checkpoint 形状不符：%s' % k)
                a[...] = v
        self.next_day = int(z['next_day'][0])
        if self.state_hash() != meta['state_sha256']:
            raise RuntimeError('checkpoint 状态 hash 不符')
        self.validate_state()
        return meta


ARM_MAP = {
    # arm: (fund, recycle, m1, m2, m3, half, rearm, route, A_ref)
    'NATIVE': (E.FD_NATIVE, E.RY_NONE, 0, 0, 0, 0, 0, 0, 0.0),
    'REINVEST_NEW': (E.FD_NATIVE, E.RY_NONE, 1, 0, 0, 0, 0, 1, 0.0),
    'REINVEST_LIQ_1E8': (E.FD_NATIVE, E.RY_NONE, 0, 1, 0, 0, 0, 1, 1e8),
    'REINVEST_LIQ_5E8': (E.FD_NATIVE, E.RY_NONE, 0, 1, 0, 0, 0, 1, 5e8),
    'EXIT_GATE_LIQ_1E8': (E.FD_NATIVE, E.RY_NONE, 0, 0, 1, 0, 0, 0, 1e8),
    'EXIT_GATE_LIQ_5E8': (E.FD_NATIVE, E.RY_NONE, 0, 0, 1, 0, 0, 0, 5e8),
    'EXIT_HALF': (E.FD_NATIVE, E.RY_NONE, 0, 0, 0, 1, 0, 0, 0.0),
    'EXIT_HALF_REARM': (E.FD_NATIVE, E.RY_NONE, 0, 0, 0, 1, 1, 0, 0.0),
    'EXIT_HALF_RECYCLE_HALF': (E.FD_NATIVE, E.RY_HALF, 0, 0, 0, 1, 0, 0, 0.0),
    'CASH_REMAIN': (E.FD_CASH, E.RY_NONE, 0, 0, 0, 0, 0, 0, 0.0),
    'RECYCLE_HALF': (E.FD_NATIVE, E.RY_HALF, 0, 0, 0, 0, 0, 0, 0.0),
}
TRIG_PANEL = {'NONE': None, 'T1a': 'T1a', 'T1b_LEVEL': 'T1b_LEVEL', 'T8': 'T8_LIMIT_CLOSE', 'UNION_T1a_T8': 'UNION_T1a_T8',
              'T8_LIMIT_CLOSE': 'T8_LIMIT_CLOSE', 'T1b_EDGE': 'T1b_EDGE'}


def ip_fp(H, trig_mode, sel=E.SM_REAL, fund=E.FD_NONE, exit_on=False, ideal=False, seed=0, shadow=False, tlog=False, recycle=E.RY_NONE,
          feedback=None, m1=0, m2=0, m3=0, half=0, rearm=0, route=0, aref=0.0, pstar=None, theta=None, qdays=None, rt=E.RT_NONE, fhit=0,
          nodes=RT_NODES):
    ip = np.zeros(E.NIP, np.int64)
    ip[E.IP_TLOG] = 1 if tlog else 0
    ip[E.IP_H] = H
    ip[E.IP_TRIG] = trig_mode
    ip[E.IP_SEL] = sel
    ip[E.IP_FUND] = fund
    ip[E.IP_LAG] = 1
    ip[E.IP_MAT] = 0
    ip[E.IP_RE] = E.RE_ALLOW
    ip[E.IP_GUARD] = E.GD_OFF
    ip[E.IP_EXIT] = 1 if exit_on else 0
    ip[E.IP_IDEAL] = 1 if ideal else 0
    ip[E.IP_RECON] = E.RC_NONE
    ip[E.IP_SEED] = seed & ((1 << 62) - 1)
    ip[E.IP_SHADOW] = 1 if shadow else 0
    ip[E.IP_NLAYER] = H
    ip[E.IP_DEPLOY] = E.DP_NONE
    ip[E.IP_CAP] = E.CP_SOURCE
    ip[E.IP_RENEW] = 0
    ip[E.IP_RECYCLE] = recycle
    ip[E.IP_FEEDBACK] = 1 if feedback else 0
    ip[E.IP_M1] = m1
    ip[E.IP_M2] = m2
    ip[E.IP_M3] = m3
    ip[E.IP_HALF] = half
    ip[E.IP_REARM] = rearm
    ip[E.IP_QDAYS] = O.QUEUE_DAYS if qdays is None else qdays
    ip[E.IP_ROUTE] = route
    ip[E.IP_RT] = rt
    ip[E.IP_FIRSTHIT] = fhit
    ip[E.IP_NODES] = nodes
    fp = np.zeros(E.NFP)
    fp[E.FP_V0] = O.V0
    fp[E.FP_FEE] = O.FEE_RATE
    fp[E.FP_SCAP] = O.STOCK_CAP
    fp[E.FP_IDEV] = O.IND_DEV
    fp[E.FP_ETA] = O.ETA_HALF
    fp[E.FP_RA] = 1e8
    fp[E.FP_RK] = 0.5
    fp[E.FP_RD] = 0.5
    fp[E.FP_P0] = O.P0_PIVOT
    fp[E.FP_PSTAR] = O.P_STAR if pstar is None else pstar
    fp[E.FP_AREF] = aref
    fp[E.FP_THETA] = O.THETA if theta is None else theta
    if feedback:
        fp[E.FP_FBA], fp[E.FP_FBK], fp[E.FP_FBD] = feedback
    return ip, fp


def spec_params(row, sel=E.SM_REAL, seed=0, shadow=False, tlog=False, feedback=None, rt=E.RT_NONE, fhit=0, pstar=None, theta=None, m1=None):
    """registry 行（dict：form / memory / H / arm / trigger / scenario）→ (ip, fp, trig_name)。trigger = NONE 的非 NATIVE 臂 = 零干预端点（无意向，与 NATIVE 同路径）。
    pstar / theta / m1 只供 S0-F 端点恒等（p* → ∞、θ = 1、new 过滤关）覆盖。"""
    H = int(float(row['H']))
    trig = row['trigger']
    fund, rmode, a1, a2, a3, hf, ra, route, aref = ARM_MAP[row['arm']]
    if m1 is not None:
        a1 = m1
    act = trig != 'NONE'
    ip, fp = ip_fp(H, E.TM_PANEL if act else E.TM_NONE, sel=sel, fund=fund, exit_on=act and not shadow,
                   ideal=row['scenario'] == 'IDEALIZED_SOURCE_FILL', seed=seed, shadow=shadow, tlog=tlog, recycle=rmode, feedback=feedback,
                   m1=a1, m2=a2, m3=a3, half=hf, rearm=ra, route=route if ((a1 or a2) and act) else 0, aref=aref, pstar=pstar, theta=theta, rt=rt,
                   fhit=fhit)
    return ip, fp, TRIG_PANEL[trig]
