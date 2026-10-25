# -*- coding: utf-8 -*-
"""E6p 合成夹具（Stage 0 的 N 类卡：S0-4 / S0-5 / S0-6 / S0-8 / S0-9 / S0-10 与 FUTURE_DATA_PLANT / MIRROR_NO_FUTURE_READ / JOURNAL_REPLAY）：
小型合成市场（与 e6p_acct.Market 同属性）+ 逐例构造；全部用生产引擎（e6p_engine）与 spec 参考函数对照，不读真实收益。"""
import numpy as np

import e6p_engine as E
import e6p_acct as A


class SynthMarket(object):
    """T 日 × N 股；价格平或随机游走；形成名单 / 自然名单 / 触发按例给定。"""

    def __init__(self, T=40, N=4, flat=False, seed=7, nclean=50.0, capsh=1.0):
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
        self.adv20 = np.full((T, N), 1e9)
        self.zsz = np.full((T, N), 0.5)
        self.ind = np.zeros((T, N), np.int16)
        self.capsh = np.full((T, 1), capsh)
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


def csr_weights(W):
    """W：(T, N) 每日 DEV 权重（> 0 入名单）→ CSR。"""
    T = W.shape[0]
    ptr = np.zeros(T + 1, np.int64)
    cols, ws = [], []
    for d in range(T):
        c = np.flatnonzero(W[d] > 0)
        cols.append(c)
        ws.append(W[d, c])
        ptr[d + 1] = ptr[d] + len(c)
    return ptr, np.concatenate(cols).astype(np.int64), np.concatenate(ws).astype(float)


def account(mk, ip, fp, trig=None, f=None, nf=None, targets=None, tgt_expo=None, lcap=4096, incap=1 << 14, tlcap=0):
    return A.Account(mk, ip, fp, trig, f, nf_csr=nf, targets=targets, tgt_expo=tgt_expo, lcap=lcap, incap=incap, tlcap=tlcap)
