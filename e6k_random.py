# -*- coding: utf-8 -*-
"""E6k 随机内容置换库（plan §10.1 / §10.2；brief W13；执行端补充 X03 / X10）。
两类分开登记（random_registry）：
  LEGACY_POLICY_RANDOM  逐位复现 E6j R-MATCH-SRC（IID、当日有效格一个 cell，E6j 稳定哈希键与 splitmix 计数器）——政策 e-随机：
      P 机制（生产六形态；E6j P 块 e6j_run_prand）：键 ('E6j.P', 成员 id, 'P_production_v2', 'native', 'IID', path)，
          当日 cell 内 u 降序第 k 个得该方向 pct 降序第 k 个（e6j_fast.Assigner）；SM 用共享 donor（'K_rar20+K_slope20'，IID:rec / IID:don）
      B 机制（R2 / A06，以及 A4b_CVRv5（= R1）上的 Q / RARPRE；E6j B 块 e6j_run_brand）：键 ('E6j.B', 成员 id, 母体（R1/R2/A06）,
          'native', 'IID', path)，donor 映射按 high_bad pct 排序（e6j_fast.DonorMapper），两方向同一 donor
  NEW_COND_*            本轮新机制：置换统一方向后的有限 kf；分区 = 自上而下分层树（变量序 I 行业 > K 旧 K3 > S size3；下一层任一叶 < 2
      则该父节点整体不细分；UNK 显式）；键 ('E6k.NEW', 测量, 分区, 块, path)——同测量全部母体 / α / H / 算子共用同一 u 流（共同随机数）；
      u 按（绝对交易日 // 块长, 规范 ticker）取值；叶内 u 降序第 k 个得 kf 降序第 k 个；缺失位置不动；多分量（SM）整行按缺失模式联合置换。
      块长 5 为主（P5），1 为 IID 独立配对对照；八子集 = {EMPTY, I, S, K, IS, IK, SK, ISK}。"""
import numpy as np

import e6j_random as RND
import e6j_fast as FAST
import e6k_env as E

_TWO53 = 9007199254740992.0
_LOW = np.uint64((1 << 53) - 1)
SUBSETS = ('EMPTY', 'I', 'S', 'K', 'IS', 'IK', 'SK', 'ISK')
E6J_MOTHER = {'A4b_CVRv5': 'R1', 'R2': 'R2', 'A06': 'A06'}
E6J_B_MEAS = ('Q', 'RARPRE20_LT', 'RARPRE60_LT', 'RARPRE20_SE', 'RARPRE60_SE')


def legacy_kind(mother, meas):
    """E6j 同对象用哪一套机制（逐位复现的前提）。"""
    if mother in ('R2', 'A06'):
        return 'B'
    if mother == 'A4b_CVRv5' and meas in E6J_B_MEAS:
        return 'B'
    return 'P'


def order_desc_stable(cellid, u):
    """= np.lexsort((−u, cellid))（含平局按原下标）：两次稳定基数排序（u 为 2^-53 整数倍，精确）。"""
    k = _LOW - (u * _TWO53).astype(np.uint64)
    o1 = np.argsort(k, kind='stable')
    return o1[np.argsort(np.asarray(cellid, np.int64)[o1], kind='stable')]


class Assigner2(object):
    """任意 cellid 的 Assigner：u 降序第 k 个得 vals 降序第 k 个（与 e6j_random.assign_by_priority 同）。"""

    def __init__(self, vals, cellid):
        self.cellid = np.asarray(cellid, np.int64)
        self.vs = vals[np.lexsort((-vals, self.cellid))]
        self.n = len(vals)

    def __call__(self, u):
        out = np.empty(self.n)
        out[order_desc_stable(self.cellid, u)] = self.vs
        return out


class DonorRows(object):
    """多分量整行：cell 内 u 降序第 k 个 recipient ← 按 donor 键（另一条 u 流）降序第 k 个 donor 的整行。"""

    def __init__(self, cellid):
        self.cellid = np.asarray(cellid, np.int64)

    def __call__(self, u_rec, u_don):
        o_r = order_desc_stable(self.cellid, u_rec)
        o_d = order_desc_stable(self.cellid, u_don)
        don = np.empty(len(o_r), np.int64)
        don[o_r] = o_d
        return don


# ====================================================================== LEGACY（E6j R-MATCH-SRC）
class Legacy(object):
    def __init__(self, seg, mother, meas, kf, kf_hi=None, kf2=None):
        self.seg, self.mother, self.meas = seg, mother, meas
        ci = seg.ci
        self.kind = legacy_kind(mother, meas)
        self.kf, self.kf2 = kf, kf2
        self.V = np.isfinite(kf) if kf2 is None else None
        if kf2 is not None:                                              # SM：共享 donor（P 机制，缺失模式分组）
            self.V1, self.V2 = np.isfinite(kf), np.isfinite(kf2)
            pat = self.V1.astype(np.int64) | (self.V2.astype(np.int64) << 1)
            self.rows = np.flatnonzero(pat > 0)
            self.cell = ci.t[self.rows].astype(np.int64) * 8 + pat[self.rows]
            self.mapper = DonorRows(self.cell)
            return
        V = self.V
        self.vt, self.vc = ci.t[V], ci.c[V]
        if self.kind == 'P':
            self.asg = FAST.Assigner(kf[V], self.vt.astype(np.int64))
        else:
            self.dm = FAST.DonorMapper(kf_hi[V], self.vt.astype(np.int64))
        self.mid = E.MEAS[meas][1]

    def key(self, path):
        if self.kf2 is not None:
            return (RND.path_key('E6j.P', 'K_rar20+K_slope20', 'P_production_v2', 'native', 'IID:rec', path),
                    RND.path_key('E6j.P', 'K_rar20+K_slope20', 'P_production_v2', 'native', 'IID:don', path))
        if self.kind == 'P':
            return RND.path_key('E6j.P', self.mid, 'P_production_v2', 'native', 'IID', path)
        return RND.path_key('E6j.B', self.mid, E6J_MOTHER[self.mother], 'native', 'IID', path)

    def draw(self, path):
        """返回置换后的 kf（SM 返回 (kS, kM)）。"""
        seg = self.seg
        g = seg.env.grid
        ci = seg.ci
        if self.kf2 is not None:
            kr, kd = self.key(path)
            r, c = ci.t[self.rows], ci.c[self.rows]
            ur = g.u_cells(kr, r, c, 1)
            ud = g.u_cells(kd, r, c, 1)
            don = self.rows[self.mapper(ur, ud)]
            o1 = np.full(seg.n, np.nan)
            o2 = np.full(seg.n, np.nan)
            o1[self.rows] = self.kf[don]
            o2[self.rows] = self.kf2[don]
            o1[~self.V1] = np.nan
            o2[~self.V2] = np.nan
            return o1, o2
        u = g.u_cells(self.key(path), self.vt, self.vc, 1)
        out = np.full(seg.n, np.nan)
        if self.kind == 'P':
            out[self.V] = self.asg(u)
        else:
            out[self.V] = self.kf[self.V][self.dm(u)]
        return out


# ====================================================================== NEW（分层树条件置换）
def tree_leaves(seg, valid, k0, subset):
    """自上而下分层树：当日为根；依变量序 I > K > S 逐层细分，下一层任一子叶有效成员 < 2 则该父节点整体不细分。
    返回每个有效单元的叶号（int64）与各层实际细分统计。"""
    ci = seg.ci
    ix = np.flatnonzero(valid)
    node = ci.t[ix].astype(np.int64)
    cats = {'I': seg.ic[ix] + 1,                                              # 0 = UNK
            'K': E.size_bins(np.where(np.isfinite(k0[ix]), np.clip(k0[ix], 1e-12, 1.0), np.nan), 3) + 1,
            'S': E.size_bins(seg.zT[ix], 3) + 1}
    order = [v for v in ('I', 'K', 'S') if v in subset] if subset != 'EMPTY' else []
    stats = {}
    for v in order:
        cat = cats[v].astype(np.int64)
        mult = int(cat.max()) + 1
        child = node * mult + cat
        uc, inv, cnt = np.unique(child, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        ccount = cnt[inv]
        # 父节点是否可细分：其全部子叶 ≥ 2
        un, ninv = np.unique(node, return_inverse=True)
        ninv = ninv.ravel()
        minc = np.full(len(un), np.iinfo(np.int64).max)
        np.minimum.at(minc, ninv, ccount)
        split = minc[ninv] >= 2
        node = np.where(split, child, node * mult)                          # 不细分者保持父节点（编码对齐到同一尺度）
        stats[v] = dict(nodes_split=int(len(np.unique(ninv[split]))), nodes_total=int(len(un)))
    _, leaf = np.unique(node, return_inverse=True)
    out = np.full(seg.n, -1, np.int64)
    out[ix] = leaf.ravel()
    return out, stats


def leaf_diagnostics(seg, leaf, valid):
    """可移动份额（叶 ≥ 2 的有效单元占比）与置换熵（Σ log n_l! 相对当日单叶 Σ log n_d! 的比例）。"""
    from scipy.special import gammaln
    ix = np.flatnonzero(valid)
    L = leaf[ix]
    cnt = np.bincount(L)
    movable = float((cnt[L] >= 2).mean()) if len(L) else np.nan
    ent_leaf = float(np.sum(gammaln(cnt + 1.0)))
    dc = np.bincount(seg.ci.t[ix], minlength=seg.T)
    ent_day = float(np.sum(gammaln(dc + 1.0)))
    return dict(movable_share=movable, entropy_ratio=ent_leaf / ent_day if ent_day > 0 else np.nan, n_leaves=int(len(cnt)))


class NewCond(object):
    """新机制内容置换：叶内按 u（绝对交易日 // 块长, ticker）降序分配 kf 降序值；缺失位置不动。"""

    def __init__(self, seg, meas, kf, k0, subset='ISK', block=5, kf2=None):
        self.seg, self.meas, self.subset, self.block = seg, meas, subset, int(block)
        self.kf, self.kf2 = kf, kf2
        ci = seg.ci
        if kf2 is None:
            V = self.V = np.isfinite(kf)
            self.leaf, self.tree_stats = tree_leaves(seg, V, k0, subset)
            self.vt, self.vc = ci.t[V], ci.c[V]
            self.asg = Assigner2(kf[V], self.leaf[V])
        else:
            self.V1, self.V2 = np.isfinite(kf), np.isfinite(kf2)
            V = self.V1 | self.V2
            self.leaf, self.tree_stats = tree_leaves(seg, V, k0, subset)
            pat = self.V1.astype(np.int64) | (self.V2.astype(np.int64) << 1)
            self.rows = np.flatnonzero(V)
            self.cell = self.leaf[self.rows] * 4 + pat[self.rows]
            self.mapper = DonorRows(self.cell)

    def key(self, path, tag=''):
        return RND.path_key('E6k.NEW', self.meas, 'COND_' + self.subset, 'B%d' % self.block, 'content' + tag, int(path))

    def draw(self, path):
        seg = self.seg
        g = seg.env.grid
        ci = seg.ci
        if self.kf2 is None:
            u = g.u_cells(self.key(path), self.vt, self.vc, self.block)
            out = np.full(seg.n, np.nan)
            out[self.V] = self.asg(u)
            return out
        r, c = ci.t[self.rows], ci.c[self.rows]
        ur = g.u_cells(self.key(path, ':rec'), r, c, self.block)
        ud = g.u_cells(self.key(path, ':don'), r, c, self.block)
        don = self.rows[self.mapper(ur, ud)]
        o1 = np.full(seg.n, np.nan)
        o2 = np.full(seg.n, np.nan)
        o1[self.rows] = self.kf[don]
        o2[self.rows] = self.kf2[don]
        o1[~self.V1] = np.nan
        o2[~self.V2] = np.nan
        return o1, o2
