# -*- coding: utf-8 -*-
"""E6k 段环境（plan §4；brief W02–W07、执行端补充 X02 / X03 / X05）。
复用 E6j 已锚部件（只 import、不改）：e6j_engine.Env（E6i 研究段 + 生产上下文，pool0 单元坐标 = (t, c) 字典序）、
e6j_engine 的三类母体结构（DepK = A4b / R1 序贯核；MeanSlot = Mmean_v2 / R2 / A06 均值核；UnionK = Munion_v2 交集核）、
e6j_slot 的测量坐标（成员原值 → pool0 当日 log 市值 OLS → 方向排名；研究坐标 NS 与生产坐标同一函数 C.precompute_neutralized_factor）。
本模块新增：
  size  z_T = 形成日 T 收盘 negMarketValue（data['mcap']）在当日 clean 域 rank(pct=True)；z_LAG1 = 前一交易日 z_T（停牌沿最近可用，记陈旧天数）
  行业  S.icodes（industry_zx1 逐日 pivot；-1 = 未知 → 显式 UNK）
  门    Struct：把三类结构拆成「门分数 → 门保留 → 下游」三段，供 SA / PM / HG / TREFIT / POST2 在实际门上接入；kept(q) 与 E6j 结构逐格相同
  合法域 / 扩展优先序（LX / RP）：E6j 同 N 合同 e6j_diag_p.matched_n（E6j plan §6.3）逐项沿用，两边各自用自己的量（执行端补充 X07）"""
import numpy as np
import pandas as pd

import e6k_core as K
import e6j_engine as EN
import e6j_slot as SL
import e6j_random as RND
import e6i_randoms as IR

P6 = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5')
P8 = P6 + ('R2', 'A06')
MEAS = {  # 键 → (来源, 成员 id, 方向 'hi' 高 = 坏 / 'lo' 低 = 坏)；plan §8.1、brief W02、执行端补充 X05
    'S': ('E6I', 'K_rar20', 'lo'),
    'M': ('E6I', 'K_slope20', 'lo'),
    'C1': ('E6I', 'K_MA3_E6F', 'hi'),
    'Q': ('J', 'J_B1_qCC', 'lo'),
    'RARPRE20_LT': ('J', 'J_B5_RARPRE_CC_W20_LT', 'lo'),
    'RARPRE60_LT': ('J', 'J_B5_RARPRE_CC_W60_LT', 'lo'),
    'RARPRE20_SE': ('J', 'J_B5_RARPRE_CC_W20_SE', 'lo'),
    'RARPRE60_SE': ('J', 'J_B5_RARPRE_CC_W60_SE', 'lo'),
}
UNK = -1


def size_bins(z, G):
    """z ∈ (0, 1] 的固定截面阈值分组：(0, 1/G] → 0 … ((G−1)/G, 1] → G−1；缺失 → UNK。"""
    out = np.full(z.shape, UNK, np.int64)
    ok = np.isfinite(z)
    out[ok] = np.clip(np.ceil(z[ok] * G - 1e-12).astype(np.int64) - 1, 0, G - 1)
    return out


def ffill_age(A):
    """(T, N) 沿时间前向填充；返回 (填充值, 距最近有效值的天数；原本有效 = 0；从未有效 = -1)。"""
    T, N = A.shape
    ok = np.isfinite(A)
    idx = np.where(ok, np.arange(T)[:, None], -1)
    last = np.maximum.accumulate(idx, axis=0)
    val = np.where(last >= 0, A[np.maximum(last, 0), np.arange(N)[None, :]], np.nan)
    age = np.where(last >= 0, np.arange(T)[:, None] - last, -1)
    return val, age


class Seg(object):
    """一段的只读上下文。所有向量都在 pool0 单元坐标（长度 n，按 (t, c) 字典序）上。"""

    def __init__(self, pname):
        self.pname = pname
        env = self.env = EN.Env(pname, with_prod=True)
        S, ci = self.S, self.ci = env.S, env.ci
        self.SE, self.ctx = env.SE, env.ctx
        self.T, self.n, self.Nc = ci.T, ci.n, ci.Nc
        self.dates = env.dates
        cnt = np.bincount(ci.t, minlength=ci.T)
        self.off = np.r_[0, np.cumsum(cnt)]
        self.tid_c = RND.ticker_ids(S.ccolnames)
        self.tid = self.tid_c[ci.c]
        if not (np.diff(self.tid_c) > 0).all():
            raise RuntimeError('ccol 次序与规范 ticker 整数次序不一致（扩展优先序的列位 = ID 前提不成立）')
        # ---- size（W03）
        mc = S.data['mcap'].astype(float).reindex(index=S.pool0.index, columns=S.pool0.columns)
        cl = S.clean.reindex(index=S.pool0.index, columns=S.pool0.columns).fillna(0) == 1
        zfull = mc.where(cl).rank(axis=1, pct=True).values
        self.zc = np.ascontiguousarray(zfull[:, S.ccols])                 # (T, Nc) 形成日 z_T（全部 clean 股，非只 pool0）
        prev = np.full(self.zc.shape, np.nan)
        prev[1:] = self.zc[:-1]
        self.zLc, self.zL_age = ffill_age(prev)                           # z_LAG1（段首日无 T−1 → NaN）
        self.zT = self.zc[ci.t, ci.c]
        self.zL = self.zLc[ci.t, ci.c]
        self.zL_stale = self.zL_age[ci.t, ci.c]
        # clean 域 z_T 五分组数量份额（EXEC_LEADER_VS_PARENT；X01 / X03）
        b5 = size_bins(zfull, 5)
        clv = cl.values
        self.share5 = np.zeros((self.T, 5))
        for g in range(5):
            self.share5[:, g] = ((b5 == g) & clv).sum(1) / np.maximum(clv.sum(1), 1)
        # ---- 行业（W05）
        self.ic = np.asarray(S.icodes)[ci.t, ci.c].astype(np.int64)         # -1 = 未知
        self.G = int(S.G)
        self._kf, self._raw, self._st = {}, {}, {}

    # ------------------------------------------------------------ 测量
    def raw(self, key):
        if key not in self._raw:
            src, mid, _ = MEAS[key]
            arr = SL.e6i_member_raw(self.pname, mid)[0] if src == 'E6I' else SL.j_member_raw(self.pname, mid)[0]
            self._raw[key] = arr
        return self._raw[key]

    def kf(self, key):
        """统一方向后的新坏度 kf（pool0 单元，缺失 NaN）= 生产坐标 pct（与 E6j P 的 member_pct、B 的 ns_pct 同一函数）。"""
        if key not in self._kf:
            _, _, d = MEAS[key]
            neu = SL.neu_of(self.ctx, SL.full_frame(self.ctx, self.raw(key)))
            self._kf[key] = self.env._dense_cells(SL.pct_dir(neu, d))
        return self._kf[key]

    def pct_on(self, raw_c, set_cells, direction):
        """COMMON_SUPPORT：原值在给定单元集合上按源口径重做 log 市值 OLS 与方向排名（E6j diag_p.cs_pct / diag_b.pct_on 同式）。"""
        import comprehensive_factor_diagnosis as C
        ci, S = self.ci, self.S
        m = np.zeros(S.pool0.shape)
        m[ci.t[set_cells], np.asarray(S.ccols)[ci.c[set_cells]]] = 1.0
        pool_J = pd.DataFrame(m, index=S.pool0.index, columns=S.pool0.columns)
        cache = C.precompute_neutralized_factor(SL.full_frame(self.ctx, raw_c), pool_J, self.ctx['log_mcap'])
        return self.env._dense_cells(SL.pct_dir(cache, direction))

    def k0_raw(self, mother):
        """母体 K 腿原值（COMMON_SUPPORT 用）：生产六形态 = conditional_turnover 源函数；R2 / A06 = 研究母体 K 腿成分。"""
        if mother in P6:
            import e6j_prod as PR
            ctx = self.ctx
            df = ctx['specs'][PR.F_COND]['func'](ctx['data'], ctx['feats'], ctx['industry'])
            return np.ascontiguousarray(df.reindex(index=self.S.pool0.index, columns=self.S.pool0.columns).values[:, self.S.ccols], dtype=np.float64)
        import e6i_ops as O
        M = self.env.R.mother(mother)
        return O._raw_c(self.S, M.core['comps'][M.leg_roles.index('K')])

    # ------------------------------------------------------------ 结构
    def struct(self, mother, q0=None):
        if q0 is not None:
            return Struct(self, mother, q0)
        if mother not in self._st:
            self._st[mother] = Struct(self, mother)
        return self._st[mother]

    # ------------------------------------------------------------ 工具
    def day_slices(self):
        return [(d, self.off[d], self.off[d + 1]) for d in range(self.T)]

    def to_cells(self, dense):
        return np.asarray(dense)[self.ci.t, self.ci.c]


class Struct(object):
    """母体结构的门拆分。kind：'A4b'（门 = K 第一关；下游 = 第二关 T 重中性化 keep b% + 否决）/
    'union'（门 = K keep 50；下游 = ∧ T / cr20 通过域 ∧ ~CVR）/ 'mean'（门 = 综合分 keep s%；下游 = ∧ ~否决）。
    门分数单位：K 坏度 pct；mean 门为三腿（R2 / A06 为两 / 三腿）均值 → b 的实际阈值 = b / 腿数（plan §5.0：生产 mean = b/3）。"""

    def __init__(self, seg, mother, q0=None):
        self.seg, self.mother = seg, mother
        env = seg.env
        if mother in P6:
            st = EN.prod_structure(env, mother, q0)
        else:
            M = env.R.mother(mother)
            i = M.leg_roles.index('K')
            legs = list(M.legs_c)
            if q0 is not None:
                legs[i] = q0
            st = EN.MeanSlot(env, legs, i, M.core['s'], M.core['fam'].startswith('KTC'), M.dr_c)
        self.st = st
        if isinstance(st, EN.DepK):
            self.kind = 'A4b'
        elif isinstance(st, EN.UnionK):
            self.kind = 'union'
        else:
            self.kind = 'mean'
        self.q0 = st.q0
        self.dom = st.dom
        self.ids = st.dom.ids
        self.nlegs = len(st.legs) if self.kind == 'mean' else 1
        self.bunit = 1.0 / (100.0 * self.nlegs)
        self.stage2 = None                     # None = IR.dep_stage2_keep（锚过的原实现）；随机层可换 e6j_fast.stage2_fast

    # ---- 三段
    def gate_scores(self, q):
        q = np.atleast_2d(q)
        if self.kind == 'mean':
            return self.st.score(q)[:, self.ids]
        return q[:, self.ids]

    def gate_keep(self, sc):
        return self.dom.keep(sc)

    def down(self, gate):
        """gate：(P, len(ids)) bool（门内成员）→ 最终名单 (P, n) bool。"""
        P = gate.shape[0]
        g = np.zeros((P, self.seg.n), bool)
        g[:, self.ids] = gate
        st = self.st
        if self.kind == 'A4b':
            k = (self.stage2 or IR.dep_stage2_keep)(self.seg.env.R, st.M, g, st.b)
            return k & ~st.drop[None, :]
        if self.kind == 'union':
            return g & st.base[None, :]
        return g & ~st.drop[None, :]

    def kept(self, q):
        return self.down(self.gate_keep(self.gate_scores(q)))

    def gate_cells(self, gate):
        g = np.zeros((gate.shape[0], self.seg.n), bool)
        g[:, self.ids] = gate
        return g

    # ---- 合法域（LX；plan §6.2）
    def legal(self):
        """pool0 技术有效域 ∩ 父子共同、不被本实验修改的过滤：
        A4b：K 有效 ∧ T 原值有效 ∧ ~否决；union：K 有效 ∧ T / cr20 通过域 ∧ ~CVR；mean：综合分有效 ∧ ~否决。"""
        st, n = self.st, self.seg.n
        ok = np.zeros(n, bool)
        ok[self.ids] = True
        if self.kind == 'A4b':
            return ok & np.isfinite(st.M.T_raw_c) & ~st.drop
        if self.kind == 'union':
            return ok & st.base
        return ok & ~st.drop

    # ---- 扩展优先序（E6j 同 N 合同 matched_n 的键；两边各用自己的量）
    def order_keys(self, q, final):
        """返回 (key1, key2, key3)（越小越优先；NaN → +inf），末级 = 列位（= 规范 ticker 次序）。q：该边的 K 坏度 (n,)；final：该边最终名单 (n,)。"""
        seg, st = self.seg, self.st
        ci = seg.ci
        n = seg.n
        if self.kind == 'mean':
            key1 = np.where(final, 0.0, 1.0)
            key2 = st.score(q[None, :])[0]
            key3 = np.zeros(n)
        elif self.kind == 'A4b':
            s1 = np.zeros(n, bool)
            s1[self.ids[self.dom.keep(q[None, self.ids])[0]]] = True
            key1 = np.where(final, 0.0, np.where(s1, 1.0, 2.0))
            x = seg.env.R.logm_c
            y = st.M.T_raw_c
            tpred = np.full(n, np.nan)
            for d in range(seg.T):
                a, b = seg.off[d], seg.off[d + 1]
                if a == b:
                    continue
                sl = np.arange(a, b)
                fit = sl[s1[sl]]
                fv = fit[np.isfinite(x[fit]) & np.isfinite(y[fit])]
                if len(fv) >= 10:
                    xm, ym = x[fv].mean(), y[fv].mean()
                    bb = np.mean((x[fv] - xm) * (y[fv] - ym)) / np.var(x[fv])
                    tpred[sl] = y[sl] - (ym - bb * xm + bb * x[sl])
                else:
                    tpred[sl] = y[sl]
            key2 = tpred
            key3 = q
        else:
            kk = np.zeros(n, bool)
            kk[self.ids[self.dom.keep(q[None, self.ids])[0]]] = True
            env = seg.env
            fails = (~kk).astype(int) + env.dT.astype(int) + env.dR.astype(int)
            key1 = np.minimum(fails, 3).astype(float)
            key2 = np.fmax(np.fmax(np.nan_to_num(q, nan=9), np.nan_to_num(env.pT, nan=9)), np.nan_to_num(env.pR, nan=9))
            key3 = np.zeros(n)
        k2 = np.where(np.isfinite(key2), key2, np.inf)
        k3 = np.where(np.isfinite(key3), key3, np.inf)
        return key1, k2, k3
