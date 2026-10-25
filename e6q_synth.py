# -*- coding: utf-8 -*-
"""E6q 合成夹具（Stage 0 的 N 类卡：S0-D / S0-E / S0-F 攻击与端点；FUTURE_DATA_PLANT / SPLIT_INVARIANCE / JOURNAL_REPLAY 等）：
小型合成市场（与 e6q_acct.Market 同属性）+ 逐例构造；全部用生产引擎（e6q_engine）跑，并与合同参考函数（plan 附录 C，e6q_contract.py）对照；不读真实收益。"""
import numpy as np

import e6q_engine as E
import e6q_acct as A


class SynthMarket(object):
    """T 日 × N 股；价格平或随机游走；形成名单 / 触发按例给定。"""

    def __init__(self, T=40, N=4, flat=False, seed=7, nclean=50.0, capsh=1.0, G=1, adv=1e9):
        self.T, self.N = T, N
        rng = np.random.default_rng(seed)
        px = np.full((T, N), 10.0) if flat else np.cumprod(1.0 + rng.normal(0, 0.01, (T, N)), axis=0) * 10.0
        self.pv = px.copy()
        self.pc = px.copy() if flat else px * 1.001
        self.pcobs = self.pc.copy()
        self.cvr = np.zeros((T, N))
        self.cpct = np.full((T, N), 0.5)
        self.sellable = np.ones((T, N), bool)
        self.buyable = np.ones((T, N), bool)
        self.isopen = np.ones((T, N), bool)
        self.sig20 = np.full((T, N), 0.02)
        self.adv20 = np.full((T, N), float(adv))
        self.zsz = np.full((T, N), 0.5)
        self.ind = np.zeros((T, N), np.int16)
        self.capsh = np.full((T, G), capsh)
        self.bench = np.zeros(T)
        self.pvage = np.zeros((T, N), np.int32)
        self.iskid = np.zeros((T, N), np.int32)
        self.n_isk = 3
        self.nclean = np.full(T, nclean)
        self.t1a = np.zeros((T, N), np.int8)
        self.lvl = np.zeros((T, N), np.int8)
        self.zero_trig = np.zeros((T, N), np.int8)
        self.nan_expo = np.full(T, np.nan)
        self.trigs = {}

    def trig(self, name):
        return self.trigs[name]


def csr_daily(T, cols, weights):
    """每日同一份名单（cols / weights）→ CSR。"""
    k = len(cols)
    ptr = np.arange(T + 1, dtype=np.int64) * k
    col = np.tile(np.asarray(cols, np.int64), T)
    w = np.tile(np.asarray(weights, float), T)
    return ptr, col, w


def account(mk, ip, fp, trig=None, f=None, targets=None, lcap=4096, incap=1 << 14, tlcap=0):
    return A.Account(mk, ip, fp, trig, f, targets=targets, lcap=lcap, incap=incap, tlcap=tlcap)


def params(H, arm='NATIVE', trig_on=True, **kw):
    """合成例用的 (ip, fp)：按 e6q_acct.ARM_MAP 取臂开关；trig_on = 是否按面板触发。kw 透传 ip_fp（pstar / theta / rt / seed / fhit / shadow / tlog / qdays）。"""
    fund, rmode, a1, a2, a3, hf, ra, route, aref = A.ARM_MAP[arm]
    return A.ip_fp(H, E.TM_PANEL if trig_on else E.TM_NONE, fund=fund, exit_on=trig_on and not kw.get('shadow', False), recycle=rmode,
                   m1=a1, m2=a2, m3=a3, half=hf, rearm=ra, route=route if ((a1 or a2) and trig_on) else 0, aref=aref, **kw)
