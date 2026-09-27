# -*- coding: utf-8 -*-
"""E6j 随机对照（plan §8.1 / §8.2；brief W08 / W14）。

种子契约（plan §8.2）：路径键 = blake2b-64(canonical_json([namespace, random_group_id, parent_canonical_id, support,
random_kind, path_index]))；不用 hash()。路径内优先序 u(路径, 绝对交易块, 股票) = splitmix64 计数器哈希
（键 ⊕ 块·C1 ⊕ ticker·C2，两轮终混，取高 53 位）：纯 uint64 整数运算、不依赖 NumPy 随机算法版本；按（绝对交易块,
规范 ticker 整数）取值 → 日期切片、重启、列重排、分片 / 并发都不改变同一股票同一日期的抽样（Stage 0 实测重放）。
  IID：块 = 绝对交易日序号；P5（稳定五日映射）：块 = 绝对交易日序号 // 5；规范 ticker = 代码去后缀（与生产 pool2 同式）。
格（cell）结构只依赖当日有效集 / 行业 / size / 旧 K 与层级规则，与路径无关，先算一次；每条路径只换 u（向量化 lexsort）。
机制：只打乱【新增分量】；母体 q0 / T / C / 缺失掩码固定，随后完成原算子（DEV / 持仓 / 成本每路径独立）。"""
import json
import hashlib

import numpy as np
import pandas as pd

_C1 = np.uint64(0xD1B54A32D192ED03)
_C2 = np.uint64(0x8CB92BA72F3D8DD7)
_G = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
_S30, _S27, _S31, _S11 = np.uint64(30), np.uint64(27), np.uint64(31), np.uint64(11)
_INV53 = 1.0 / 9007199254740992.0
GEN_ID = 'splitmix64x2-counter(key^block*C1^ticker*C2)>>11 * 2^-53; key=blake2b-64(canonical_json)'


def path_key(namespace, group, parent, support, kind, path):
    s = json.dumps([namespace, group, parent, support, kind, int(path)], sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return int.from_bytes(hashlib.blake2b(s.encode('ascii'), digest_size=8).digest(), 'big')


def _splitmix(z):
    with np.errstate(over='ignore'):
        z = z + _G
        z = (z ^ (z >> _S30)) * _M1
        z = (z ^ (z >> _S27)) * _M2
        return z ^ (z >> _S31)


def uniform(key, blocks, tids):
    b = np.asarray(blocks, dtype=np.uint64); t = np.asarray(tids, dtype=np.uint64)
    with np.errstate(over='ignore'):
        z = np.uint64(key) ^ (b * _C1) ^ (t * _C2)
    return (_splitmix(_splitmix(z)) >> _S11).astype(np.float64) * _INV53


def ticker_ids(columns):
    return np.array([int(str(c).split('.')[0]) for c in columns], dtype=np.int64)


def day_index(dates, calendar):
    pos = pd.Index(calendar).get_indexer(pd.Index(dates))
    if (pos < 0).any():
        raise RuntimeError('日期不在全样本交易日历内')
    return pos.astype(np.int64)


class Grid(object):
    """一段的随机坐标：有效格扁平化（行优先）、绝对交易日序号、规范 ticker 整数。"""

    def __init__(self, dates, columns, calendar):
        self.day = day_index(dates, calendar)
        self.tid = ticker_ids(columns)
        self.T, self.N = len(dates), len(columns)

    def u_cells(self, key, rows, cols, block_days=1):
        return uniform(key, self.day[rows] // int(block_days), self.tid[cols])


# ------------------------------------------------------------------ 格内按优先序分配（向量化）
def assign_by_priority(vals, cellid, u):
    """扁平有效格：同一 cell 内，u 降序第 k 个得到 vals 降序第 k 个值（有序值按优先序分配）。"""
    o_u = np.lexsort((-u, cellid))
    o_v = np.lexsort((-vals, cellid))
    out = np.empty_like(vals)
    out[o_u] = vals[o_v]
    return out


def day_cells(valid):
    """IID / P5：cell = 当日（全部当日有效格一个 cell）。返回扁平 (rows, cols, cellid)。"""
    rows, cols = np.nonzero(valid)
    return rows, cols, rows.astype(np.int64)


def terciles_rowwise(x, valid):
    q = np.full(x.shape, -1, dtype=np.int64)
    for t in range(x.shape[0]):
        idx = np.flatnonzero(valid[t] & np.isfinite(x[t]))
        if len(idx) < 3:
            continue
        r = pd.Series(x[t, idx]).rank(method='first').to_numpy()
        q[t, idx] = np.minimum((3 * (r - 1) // len(idx)).astype(np.int64), 2)
    return q


def cond_cells(valid, ind, size, oldk):
    """R-COND 不重叠分区（plan §8.1）：层 0 行业×size3×K3 → 层 1 行业×K3 → 层 2 行业 → 层 3 全池；
       每层只在尚未分配的格里组格，格内合格 donor ≥ 2 才成格，否则留给下一层；层 3 单只 = 恒等（无随机自由度）。
       行业缺失（< 0）是显式类别。返回 (rows, cols, cellid, layer)。与路径无关。"""
    rows, cols = np.nonzero(valid)
    s3 = terciles_rowwise(size, valid)[rows, cols]; k3 = terciles_rowwise(oldk, valid)[rows, cols]
    ii = ind[rows, cols].astype(np.int64)
    n = len(rows)
    cell = np.full(n, -1, dtype=np.int64); layer = np.full(n, -1, dtype=np.int64)
    keys = [np.stack([rows, ii, s3, k3], 1), np.stack([rows, ii, k3], 1), np.stack([rows, ii], 1), rows[:, None]]
    left = np.ones(n, bool); next_id = 0
    for L, K in enumerate(keys):
        if not left.any():
            break
        sub = np.flatnonzero(left)
        _, inv, cnt = np.unique(K[sub], axis=0, return_inverse=True, return_counts=True)
        inv = inv.ravel()
        ok = (cnt[inv] >= 2) | (L == 3)
        take = sub[ok]
        cell[take] = next_id + inv[ok]; layer[take] = L
        next_id += len(cnt)
        left[take] = False
    return rows, cols, cell, layer


def permuted_matrix(vals, valid_rows, valid_cols, cellid, u, shape):
    """把扁平的分配结果写回 (T, N)；有效格外 NaN。"""
    out = np.full(shape, np.nan)
    v = vals[valid_rows, valid_cols]
    out[valid_rows, valid_cols] = assign_by_priority(v, cellid, u)
    return out


def shared_donor_matrix(cols_vals, valid_each, grid, key_rec, key_don, block_days):
    """SM 共享 donor（plan §8.1）：按缺失模式（全有效 / 只 S / 只 M）分组，组内 recipient（u_rec 降序）取 donor（u_don 降序）
       的整行向量；两列共用同一 donor 映射，不分别排序。"""
    pat = np.zeros(cols_vals[0].shape, dtype=np.int64)
    for j, v in enumerate(valid_each):
        pat |= (v.astype(np.int64) << j)
    rows, cols = np.nonzero(pat > 0)
    cell = rows.astype(np.int64) * 8 + pat[rows, cols]
    ur = grid.u_cells(key_rec, rows, cols, block_days); ud = grid.u_cells(key_don, rows, cols, block_days)
    o_r = np.lexsort((-ur, cell)); o_d = np.lexsort((-ud, cell))
    outs = []
    for j, v in enumerate(cols_vals):
        o = np.full(v.shape, np.nan)
        src = v[rows[o_d], cols[o_d]]
        o[rows[o_r], cols[o_r]] = src
        o[~valid_each[j]] = np.nan
        outs.append(o)
    return outs


# ------------------------------------------------------------------ 编辑随机（EDIT-ENTRY / EDIT-BOTH）
def _rank_within(g):
    """g：组号（整数）；返回每个元素在其组内按原次序的名次（0 起）与稳定排序的次序。"""
    o = np.argsort(g, kind='stable')
    gs = g[o]
    st = np.r_[True, gs[1:] != gs[:-1]] if len(gs) else np.zeros(0, bool)
    first = np.flatnonzero(st)
    gid = np.cumsum(st) - 1
    r = np.empty(len(g), dtype=np.int64)
    r[o] = np.arange(len(gs)) - first[gid]
    return r


def _pick_levels(cand_rows, cand_cols, cand_keys, need_rows, need_keys, u_c):
    """分层配额抽样（配额与路径无关，u 与路径有关；全向量化）：cand_keys / need_keys 为各层键（逐层变粗，最后一层 = 日）。
       逐层：同一键内，按 u 降序从尚未被选的候选里取 min(需求, 可用) 个；被满足的需求按原次序划掉，其余留到下一层
       （同一细键的需求共享全部粗键，划掉哪几个不影响后续层）。返回被选候选下标与逐日 shortfall。"""
    taken = np.zeros(len(cand_rows), bool)
    need_left = np.ones(len(need_rows), bool)
    for L in range(len(cand_keys)):
        if not need_left.any():
            break
        avail = np.flatnonzero(~taken)
        nidx = np.flatnonzero(need_left)
        allk = np.vstack([cand_keys[L][avail], need_keys[L][nidx]])
        _, inv = np.unique(allk, axis=0, return_inverse=True)
        inv = inv.ravel()
        ic, ineed = inv[:len(avail)], inv[len(avail):]
        quota = np.bincount(ineed, minlength=int(inv.max()) + 1)
        o = np.lexsort((-u_c[avail], ic))
        rk = np.empty(len(avail), dtype=np.int64)
        rk[o] = _rank_within(ic[o])
        sel = rk < quota[ic]
        taken[avail[sel]] = True
        got = np.bincount(ic[sel], minlength=len(quota))
        sat = _rank_within(ineed) < got[ineed]
        need_left[nidx[sat]] = False
    short = np.bincount(need_rows[need_left]) if need_left.any() else np.zeros(0, dtype=np.int64)
    return np.flatnonzero(taken), short


def _level_keys(rows, cols, ind, k3):
    ii = ind[rows, cols].astype(np.int64); kk = k3[rows, cols]
    return [np.stack([rows, ii, kk], 1), np.stack([rows, kk], 1), np.stack([rows, ii], 1), rows[:, None]]


def edit_entry(parent, child, legal, grid, key, ind, oldk, block_days=5, k3=None):
    """EDIT-ENTRY：固定 D = B\\C 与 I = B∩C；从 U\\B 按真实换入者（行业×旧 K 三档）人数抽 |C\\B|，不足依次并层。
       k3 可预先算好（只依赖旧 K 与合法域，与路径无关）。"""
    if k3 is None:
        k3 = terciles_rowwise(oldk, legal)
    I = parent & child
    ar, ac = np.nonzero(child & ~parent)
    cr, cc = np.nonzero(legal & ~parent)
    u = grid.u_cells(key, cr, cc, block_days)
    chosen, short = _pick_levels(cr, cc, _level_keys(cr, cc, ind, k3), ar, _level_keys(ar, ac, ind, k3), u)
    out = I.copy()
    out[cr[chosen], cc[chosen]] = True
    return out, short


def edit_both(parent, child, legal, grid, key_out, key_in, ind, oldk, block_days=5, k3=None):
    """EDIT-BOTH：从 B 抽 |D| 个换出（匹配真实换出者粗层），从 U\\B 抽 |A| 个换入（匹配真实换入者粗层）。"""
    if k3 is None:
        k3 = terciles_rowwise(oldk, legal)
    dr, dc = np.nonzero(parent & ~child)
    br, bc = np.nonzero(parent)
    uo = grid.u_cells(key_out, br, bc, block_days)
    dsel, s1 = _pick_levels(br, bc, _level_keys(br, bc, ind, k3), dr, _level_keys(dr, dc, ind, k3), uo)
    out = parent.copy()
    out[br[dsel], bc[dsel]] = False
    ar, ac = np.nonzero(child & ~parent)
    cr, cc = np.nonzero(legal & ~parent)
    ui = grid.u_cells(key_in, cr, cc, block_days)
    asel, s2 = _pick_levels(cr, cc, _level_keys(cr, cc, ind, k3), ar, _level_keys(ar, ac, ind, k3), ui)
    out[cr[asel], cc[asel]] = True
    return out, (s1, s2)
