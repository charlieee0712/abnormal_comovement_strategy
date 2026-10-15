# -*- coding: utf-8 -*-
"""E6n 随机层（plan §7.1、§6.4a；brief W12、§1.3-9、§7；附录 A5）。随机的是新增信息：源 Q0、旧 K / T / CVR、原资格不随机。
一段一个父进程（段环境 e6l_env.SegL、测量基表 e6n_vars.Base、六形态结构一次加载）→ fork 进程池（写时复制共享）→
任务 = (机制, 载荷组, 路径区间)；任务内对该组全部登记名单键（六形态 × 记忆 × α × 变体 [× 分量控制]）逐路径重跑：
置换 → 源中性化 / 方向排名（pct_src：与源 C.precompute_neutralized_factor + neutralize_by_mcap + pct_dir 同一组 numpy 调用，残差逐位相同）
→ 生成语法（e6n_vars 同式）→ 门（Struct.gate_scores）→ 稳定全序 / 无带门 U（e6l_fast.order_U）→ 记忆（e6l_fast.rec_single：HG 读本路径 G_{t−1}、
LAG1 读本路径自然 U_{t−1}）→ 下游（e6l_fast.StructFast.down）→ DEV + 多 H 账本（e6l_fast.AcctFast；逐路径独立收费）→ e6l_run_rand.accum_nb 同构累加。
E6l Stage 0 已在真实数据上核 order_U / rec_single / down / acct 与参照实现逐位相同；本轮 selftest 再以"恒等 donor"在真实数据上把整条管道
与已交名单（masks/<段>/<形态>.npz）逐格对拍（不读收益）。

机制（random_manifest_E6n.csv 逐行登记）：
  CONTENT_IID         owner 可动域内当日一层；u = path_key('E6n.CONTENT_IID', 组, 'ALL_FORMS', 支持, 'IID', p) 的（绝对交易日, ticker）哈希
  CONTENT_ISK_P5      层 = 行业 × size3 × 旧 K3（当日 pool0 中分布三分，缺 = 第 4 档）；u 的块 = 绝对交易日 // 5；层 < 2 不动；行业未知只在未知层内
  CONTENT_QRANGE_P5   层 = 行业 × 源 Q3（kQ）× 当日 range3（log(H/L)）；同 P5；只覆盖主 72 新行与两条适应构造 CORE 全 H（登记表 random_mechanisms）
  R_MEMORY            主 72 带记忆行：真实内容；HG = 本路径 G_{t−1}、LAG = 本路径自然 U_{t−1} 的标记数在门域内按 P5 u 置换（计数守恒）
  LEGACY_POLICY_RANDOM 源政策随机合同（E6l / E6m 对新测量的 P 机制：形成日内 IID 置换对象自身 Q 槽测量 kf，成员键 'E6n.<变体>'）——
                      只供原资格 e随机项；与新增内容诊断随机分开登记，不互相替代（plan §7.1 末段）
载荷组（共享 donor = 共同随机数；matched 控制与 owner 同 donor，COMPONENT_DOSE 逐路径重算目标矩）：
  FACET|<面>|<作用域>|f<频率>   五面 / OHLC 桥：同 donor 的有限 raw 观测（中性化之前）整值移动；方向 ±1 共用同一置换
  RAW|<支持族>|<作用域>|f<频率>  族内 Q_PATH / Q_RV / Q_RANGE / Q_CLOSE_THIN / Q_CLOSE_LEVEL / Q_BOTH / COMBO：同 donor 整行（h_path, sqrtRV, log(H/L),
                               h_close, u_close）；recipient 保留 d / ε / λ
可动域 = owner 激活集（作用域 ∧ 支持族技术可算 ∧ 源 Q 可用），置换只在可动域内；donor 映射 = 层内 recipient 按 u 降序第 k 个 ← 层内按 ticker 升序第 k 个
（同一 P5 块内层成分不变则 donor 不变；块哈希不保证五天 donor 不变 → 逐日 donor 更换率 / 自配率 / 真移动比例写 donor 日志）。
输出 randoms/<机制>/<段>/<组>__p<起>_<数>.npz（E6l 同格式 + form / mask_key / table）+ donor_<…>.npz；回执 E6n_rand_<机制>_<段>_<组>_p<起>_<数>。"""
import os
import sys
import json
import time
import hashlib
import argparse
import resource
import multiprocessing as mp

import numpy as np
import numba as nb
import pandas as pd

import e6n_core as N
import e6n_vars as VR
import e6n_masks as MK

MECHS_CONTENT = ('CONTENT_IID', 'CONTENT_ISK_P5', 'CONTENT_QRANGE_P5')
MECHS = MECHS_CONTENT + ('R_MEMORY', 'LEGACY_POLICY_RANDOM')
PARENTS6 = MK.PARENTS6
BATCH = 32                      # 一批路径（门 / 下游 / 账本同批）；分片常量只此一处（#102）
CHUNK = 128                     # 一个任务的路径数（主批 1,024 = 8 片；增补 512 = 4 片）
FIRST = 1024
TOPUP = 512
MAXP = 8192
MCSE_MAX = 0.03
AUDIT_PATHS = (0, 1)
DONOR_LOG_PATHS = 8             # 每 (机制, 组, 段) 前 8 条路径写逐日 donor 日志
CTX = {}
NJ = dict(cache=True, error_model='numpy', nogil=True)


# ====================================================================== 源排名（逐位）
@nb.njit(**NJ)
def avg_rank_pct(v):
    """pandas Series.rank(method='average', pct=True)（NaN 已剔）：并列段平均位次 = (i + j)/2 + 1（精确），再 / n。"""
    n = len(v)
    out = np.empty(n)
    if n == 0:
        return out
    o = np.argsort(v, kind='mergesort')
    i = 0
    while i < n:
        j = i
        while j + 1 < n and v[o[j + 1]] == v[o[i]]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[o[k]] = r / n
        i = j + 1
    return out


def pct_src(vals, lm, off, direction):
    """单元向量（pool0 单元，按 (t, c) 字典序；pool = pool0 全部单元）→ 源坐标 pct（缺 NaN）。
    逐日：pool 成员 < 6 → 跳过；neutralize_by_mcap：(f, m) 双有限 < 10 或 var(x) < 1e−10 → 原值；否则 β = cov(x, y, bias)[0,1] / var(x)、
    α = mean(y) − β·mean(x)、残差（与源同一组 numpy 调用、同数组次序 → 逐位）；剔 NaN 后 < 6 → 跳过；'hi' = rank(pct)，'lo' = (−s).rank(pct)。"""
    out = np.full(len(vals), np.nan)
    neg = direction == 'lo'
    for d in range(len(off) - 1):
        a, b = int(off[d]), int(off[d + 1])
        if b - a < 6:
            continue
        f = vals[a:b]
        m = lm[a:b]
        both = np.isfinite(f) & np.isfinite(m)
        res = None
        if int(both.sum()) >= 10:
            x = m[both]
            y = f[both]
            var_x = np.var(x)
            if not var_x < 1e-10:
                beta = np.cov(x, y, bias=True)[0, 1] / var_x
                alpha = y.mean() - beta * x.mean()
                res = np.full(b - a, np.nan)
                res[both] = y - (alpha + beta * x)
        if res is None:
            res = f
        fin = np.isfinite(res)
        k = int(fin.sum())
        if k < 6:
            continue
        v = res[fin]
        if neg:
            v = -v
        out[a + np.flatnonzero(fin)] = avg_rank_pct(np.ascontiguousarray(v))
    return out


# ====================================================================== 分层坐标与 donor
def terc_mid(x, off):
    """逐日中分布位置三分（plan §6.1：u = (#更小 + 0.5·#相等)/n，组 = min(2, floor(3u))；全等落中组）；缺失 = 3。"""
    out = np.full(len(x), 3, np.int64)
    for d in range(len(off) - 1):
        a, b = int(off[d]), int(off[d + 1])
        v = x[a:b]
        ok = np.isfinite(v)
        n = int(ok.sum())
        if n == 0:
            continue
        s = np.sort(v[ok])
        lt = np.searchsorted(s, v[ok], 'left')
        le = np.searchsorted(s, v[ok], 'right')
        u = (lt + 0.5 * (le - lt)) / n
        g = np.minimum(2, np.floor(3 * u)).astype(np.int64)
        tmp = np.full(b - a, 3, np.int64)
        tmp[ok] = g
        out[a:b] = tmp
    return out


def strata(mech, t, ind, size3, k3, q3, r3, G):
    """单元 → 层号（含日）。IID：日；ISK：日 × 行业 × size3 × 旧 K3；QRANGE：日 × 行业 × Q3 × range3。行业 −1 = 未知层。"""
    t = t.astype(np.int64)
    if mech in ('CONTENT_IID',):
        return t
    i1 = ind.astype(np.int64) + 1
    if mech == 'CONTENT_ISK_P5':
        return ((t * (G + 1) + i1) * 4 + size3) * 4 + k3
    if mech == 'CONTENT_QRANGE_P5':
        return ((t * (G + 1) + i1) * 4 + q3) * 4 + r3
    raise ValueError(mech)


def donor_map(dom_idx, strat, u):
    """可动域单元 dom_idx（升序）→ donor 单元（同长）：层内 u 降序第 k 个 recipient ← 层内单元号升序第 k 个 donor。"""
    o_r = np.lexsort((-u, strat))
    o_d = np.lexsort((dom_idx, strat))
    don = np.empty(len(dom_idx), np.int64)
    don[o_r] = dom_idx[o_d]
    return don


def donor_log(dom_idx, don, t, c, strat, T):
    """逐日：可动格数、真移动比例（donor ≠ 自身）、自配率、donor 更换率（今昨都在域的 recipient 中 donor 列变化份额）、层 < 2 的格份额。"""
    out = np.full((T, 5), np.nan)
    dt = t[dom_idx]
    self_ = don == dom_idx
    _, inv, cnt = np.unique(strat, return_inverse=True, return_counts=True)
    single = cnt[inv] < 2
    prev = {}
    for d in np.unique(dt):
        sl = np.flatnonzero(dt == d)
        n = len(sl)
        cur = {int(c[dom_idx[i]]): int(c[don[i]]) for i in sl}
        ch = [cur[k] != prev[k] for k in cur if k in prev]
        out[d] = (n, 1.0 - self_[sl].mean(), self_[sl].mean(), (np.mean(ch) if ch else np.nan), single[sl].mean())
        prev = cur
    return out


# ====================================================================== 登记 → 组 / 任务
def group_of_variant(v):
    p = v.split('|')
    if p[0] == 'FACET':
        return 'FACET|%s|%s|%s' % (p[1], p[3], p[4])
    if p[0] == 'RAW':
        return 'RAW|%s|%s|%s' % (p[5][4:], p[3], p[4])
    if p[0] == 'CDOSE':
        return group_of_variant('|'.join(p[1:]))
    raise ValueError(v)


def manifest():
    """random_manifest_E6n：每行 = (机制, 组, 形态, 名单键, 对象, 表, H)。主随机绑定对象（CORE … FREQUENCY）× IID / ISK；
    QRANGE 按登记 random_mechanisms；分量（MATCHED_COMPONENT / COMPONENT_DOSE）随 owner 组共享 donor（IID / ISK；QRANGE 只 owner）；
    R_MEMORY = r_memory 行；LEGACY_POLICY_RANDOM = 进政策表的随机绑定主对象（原资格 e随机项）。"""
    R = MK.registry_rows()
    D = pd.read_csv(N.P('registry', 'descriptors_E6n.csv'), keep_default_na=False)
    C = pd.read_csv(N.P('registry', 'component_controls_E6n.csv'), keep_default_na=False)
    dm = D.set_index('desc_id')
    rb = set(D.desc_id[D.random_bound.astype(str) == 'True'])
    comp = set(C.comp_id)
    rows = []
    for r in R.itertuples():
        if r.table == 'MAIN' and r.obj in rb:
            mechs = dm.at[r.obj, 'random_mechanisms'].split('|')
            if str(dm.at[r.obj, 'r_memory']) == 'True':
                mechs = mechs + ['R_MEMORY']
            if str(dm.at[r.obj, 'in_policy_table']) == 'True':
                mechs = mechs + ['LEGACY_POLICY_RANDOM']
        elif r.table == 'COMP' and r.obj in comp:
            mechs = ['CONTENT_IID', 'CONTENT_ISK_P5']
        else:
            continue
        var = r.variant if not r.variant.startswith('CDOSE') else r.variant
        g = group_of_variant(var)
        for m in mechs:
            rows.append(dict(mechanism=m, group=('RMEM' if m == 'R_MEMORY' else g), form=r.parent, mask_key=r.mask_key, obj=r.obj, table=r.table,
                             H=int(r.H), variant=r.variant, ctrl=r.ctrl or 'NOT_APPLICABLE', memory=r.memory, alpha=float(r.alpha_eff)))
    M = pd.DataFrame(rows)
    M['key_namespace'] = 'E6n.' + M.mechanism
    M['block_days'] = M.mechanism.map({'CONTENT_IID': 1, 'CONTENT_ISK_P5': 5, 'CONTENT_QRANGE_P5': 5, 'R_MEMORY': 5, 'LEGACY_POLICY_RANDOM': 1})
    M['strata'] = M.mechanism.map({'CONTENT_IID': 'DAY', 'CONTENT_ISK_P5': 'DAY×INDUSTRY×SIZE3×OLDK3', 'CONTENT_QRANGE_P5': 'DAY×INDUSTRY×SRCQ3×RANGE3',
                                   'R_MEMORY': 'GATE_DOMAIN', 'LEGACY_POLICY_RANDOM': 'DAY（E6l / E6m 新测量 P 机制）'})
    M['payload'] = np.where(M.mechanism.isin(MECHS_CONTENT), np.where(M.group.str.startswith('FACET'), 'RAW_FACET_OBS_PRE_NEUTRALIZATION',
                                                                      'RAW_ROW(h_path,sqrtRV,log_hl,h_close,u_close)'),
                            np.where(M.mechanism == 'R_MEMORY', 'PREV_DAY_IDENTITY(HG=G_t-1,LAG=U_t-1)', 'OWN_QSLOT_KF'))
    M['first_paths'] = FIRST
    M['topup_paths'] = TOPUP
    M['max_paths'] = MAXP
    M['mcse_target_ann_pp'] = MCSE_MAX
    return M


# ====================================================================== 段上下文（父进程一次）
def load_ctx(seg_name, forms=PARENTS6, acct=True):
    import e6l_env as V
    import e6l_fast as FA
    t0 = time.time()
    seg = V.SegL(seg_name, state=False)
    B = VR.Base(seg_name)
    if not (np.array_equal(seg.ci.t, B.t) and np.array_equal(seg.ci.c, B.c)):
        raise RuntimeError('段单元坐标与测量单元不一致')
    import e6n_meas as ME
    S = ME.SegM(seg_name)
    lm = S.cells(S.ctx['log_mcap'].reindex(index=S.pool0.index, columns=S.pool0.columns).to_numpy(float)[:, S.ccols])
    off = np.r_[0, np.cumsum(np.bincount(B.t, minlength=S.T))].astype(np.int64)
    structs = {}
    for f in forms:
        st = seg.struct(f)
        structs[f] = (st, FA.StructFast(st))
        q0 = np.asarray(st.q0, float)
        k0 = B.get('k0')
        if not ((np.isfinite(q0) == np.isfinite(k0)).all() and (q0[np.isfinite(q0)] == k0[np.isfinite(k0)]).all()):
            raise RuntimeError('st.q0 ≠ 测量 k0（%s）' % f)
    AF = FA.AcctFast(seg) if acct else None              # selftest 不建账本输入（不读收益）
    FA.warmup()
    avg_rank_pct(np.array([1.0, 0.0, 1.0]))
    ind = np.asarray(seg.ic, np.int64)
    G = int(seg.G)
    coords = dict(ind=ind, G=G, size3=terc_mid(lm, off), k3=terc_mid(B.get('k0'), off), q3=terc_mid(B.kQ, off),
                  r3=terc_mid(B.get('col_LOG_HL'), off))
    CTX.update(seg=seg, B=B, lm=lm, off=off, structs=structs, AF=AF, coords=coords, seg_name=seg_name, t_env=time.time() - t0,
               tday=seg.env.grid.day[B.t].astype(np.int64), tid=np.asarray(seg.tid, np.int64))
    return CTX


def u_cells(key, cells, block):
    import e6j_random as RND
    return RND.uniform(key, CTX['tday'][cells] // int(block), CTX['tid'][cells])


def path_key(mech, group, support, kind, p):
    import e6j_random as RND
    return RND.path_key('E6n.' + mech, group, 'ALL_FORMS', support, kind, int(p))


# ====================================================================== 组：可动域、载荷、逐路径 kf
class Group(object):
    def __init__(self, gkey, variants):
        B = CTX['B']
        self.gkey = gkey
        p = gkey.split('|')
        self.family, self.feature, self.app, self.fr = p[0], p[1], p[2], int(p[3][1:])
        self.variants = sorted(set(variants))
        if self.family == 'FACET':
            km = B.get(VR.km_name(self.feature, self.fr, 1))
            self.dom = B.active_dom(self.app) & np.isfinite(km) & np.isfinite(B.kQ)
            self.raw = B.get('raw_%s_f%d' % (self.feature, self.fr))
            for v in self.variants:
                if v.startswith('FACET') and not np.array_equal(VR.facet(B, v)[1], self.dom):
                    raise RuntimeError('FACET 变体激活集 ≠ 组可动域：%s' % v)
        else:
            fam = self.feature
            self.dom = (B.active_dom(self.app) & VR.support_mask(B, fam, self.fr) & np.isfinite(B.dd) & np.isfinite(B.kQ) & np.isfinite(B.q0raw))
            self.mismatch = {}
            self.act_real = {}
            for v in self.variants:
                vv = v if v.startswith('RAW') else '|'.join(v.split('|')[1:])
                act = VR.raw_active(B, vv)[0]
                self.act_real[vv] = act
                self.mismatch[vv] = int((self.dom != act).sum())
        self.dom_idx = np.flatnonzero(self.dom).astype(np.int64)
        self.support = '%s|f%d' % (self.app, self.fr)

    def donors(self, mech, p):
        """→ donor 单元（可动域上）；层号。"""
        B = CTX['B']
        co = CTX['coords']
        di = self.dom_idx
        st = strata(mech, B.t[di], co['ind'][di], co['size3'][di], co['k3'][di], co['q3'][di], co['r3'][di], co['G'])
        blk = 1 if mech == 'CONTENT_IID' else 5
        u = u_cells(path_key(mech, self.gkey, self.support, 'IID' if blk == 1 else 'P5', p), di, blk)
        return donor_map(di, st, u), st

    def kf_path(self, don, cache, identity=False):
        """一条路径：组内全部变体的 kf（dict 变体 → 单元向量）。identity = 恒等 donor（selftest）。"""
        B = CTX['B']
        lm, off = CTX['lm'], CTX['off']
        di = self.dom_idx
        out = {}
        if self.family == 'FACET':
            R = self.raw.copy()
            if not identity:
                R[di] = self.raw[don]
            km = {}
            for v in self.variants:
                q = VR.parse(v)
                dr = 'hi' if q['dir'] > 0 else 'lo'
                if dr not in km:
                    km[dr] = pct_src(R, lm, off, dr)
                out[v] = np.where(self.dom, (1.0 - q['eta']) * B.kQ + q['eta'] * km[dr], B.kQ)
            return out
        for v in self.variants:
            vv = v if v.startswith('RAW') else None
            if vv is None:
                continue
            q = VR.parse(vv)
            h = VR.raw_h(B, q['feature'], q['fr'])
            hp = h.copy()
            if not identity:
                hp[di] = h[don]
            act = self.dom & np.isfinite(hp) & (np.nan_to_num(hp, nan=-1.0) >= 0)
            raw = B.q0raw.copy()
            raw[act] = 1.0 / (B.dd[act] + q['lam'] * hp[act] + VR.EPS)
            kn = pct_src(raw, lm, off, 'lo')
            out[vv] = np.where(act, kn, B.kQ)
            cache[vv] = act
        return out


# ====================================================================== 门层（一批路径）
def gate_final(form, memory, alpha, KF, variant, ctrl, KFC=None, act=None):
    """KF：(P, n) 本批各路径 kf（或 None = 真实内容广播）→ 最终名单 (P, n)。"""
    import e6l_fast as FA
    st, SF = CTX['structs'][form]
    seg = CTX['seg']
    k0 = np.asarray(st.q0, float)
    a = float(alpha)
    if variant.startswith('CDOSE'):
        Q = cdose_batch(k0, CTX['B'].kQ, KF, KFC, act, a, CTX['B'].t)
    else:
        Q = np.where(np.isfinite(KF), (1 - a) * k0[None, :] + a * KF, k0[None, :])
    SC = np.ascontiguousarray(st.gate_scores(Q))
    O, U = FA.order_U(SC, SF.off, SF.K)
    if memory == 'NONE':
        G = U
    else:
        be = np.full(seg.T, 10.0 * st.bunit)
        G = FA.rec_single(SC, O, U, SF.off, SF.K, SF.cols, be, SF.Nc, memory == 'LAG1_10')
    return SF.down(G)


def gate_only(form, memory, alpha, KF):
    """门名单 (P, len(ids))（不经下游；Stage 0 A3-3 用）。"""
    import e6l_fast as FA
    st, SF = CTX['structs'][form]
    k0 = np.asarray(st.q0, float)
    a = float(alpha)
    Q = np.where(np.isfinite(KF), (1 - a) * k0[None, :] + a * KF, k0[None, :])
    SC = np.ascontiguousarray(st.gate_scores(Q))
    O, U = FA.order_U(SC, SF.off, SF.K)
    if memory == 'NONE':
        return U
    be = np.full(CTX['seg'].T, 10.0 * st.bunit)
    return FA.rec_single(SC, O, U, SF.off, SF.K, SF.cols, be, SF.Nc, memory == 'LAG1_10')


def cdose_batch(k0, kQ, KFO, KFC, act, a, t):
    """e6n_vars.cdose_K 的批量版（逐日 (P, m) 行向约简 = 逐路径 1-D 约简，同 pairwise 求和）：每路径用自己的 owner / 控制矩。"""
    P = KFO.shape[0]
    SQ = VR.native_q(k0, kQ, a)
    SO = np.where(np.isfinite(KFO), (1 - a) * k0[None, :] + a * KFO, k0[None, :])
    SG = np.where(np.isfinite(KFC), (1 - a) * k0[None, :] + a * KFC, k0[None, :])
    out = np.repeat(SQ[None, :], P, axis=0)
    ok = act & np.isfinite(SQ) & np.isfinite(SO).all(0) & np.isfinite(SG).all(0)
    ix = np.flatnonzero(ok)
    if not len(ix):
        return out
    tt = t[ix]
    bnd = np.flatnonzero(np.r_[True, tt[1:] != tt[:-1], True])
    for i0, i1 in zip(bnd[:-1], bnd[1:]):
        sl = ix[i0:i1]
        for p in range(P):
            m = VR.dose_match(SG[p, sl] - SQ[sl], SO[p, sl] - SQ[sl])
            if m is None:
                continue
            out[p, sl] = SQ[sl] + m
    return out


# ====================================================================== R_MEMORY（LAG 版：标记 = 本路径自然 U_{t−1}）
@nb.njit(**NJ)
def rec_rmark_lag(sc, O, U, off, K, cols, be_day, Nc, grp, uu):
    """e6l_fast.rec_rmark 的 LAG 版：标记来源 = 同算子昨日无优惠自然 U（与内容无关，故路径间相同），在当日分组内按 key = g·2 + (1 − u) 稳定序的前 m_g 名得标记。"""
    P, Nn = sc.shape
    T = len(K)
    G = np.zeros((P, Nn), np.bool_)
    mmax = 1
    for d in range(T):
        if off[d + 1] - off[d] > mmax:
            mmax = off[d + 1] - off[d]
    mark = np.zeros(mmax, np.bool_)
    key = np.empty(mmax)
    mg = np.zeros(mmax + 1, np.int64)
    cg = np.zeros(mmax + 1, np.int64)
    ust = np.empty(Nc, np.int64)
    for p in range(P):
        ust[:] = -1000000
        for d in range(T):
            a = off[d]
            m = off[d + 1] - a
            if m == 0 or K[d] == 0:
                continue
            ng = 0
            for r in range(m):
                if grp[a + r] + 1 > ng:
                    ng = grp[a + r] + 1
            for g in range(ng):
                mg[g] = 0
                cg[g] = 0
            for r in range(m):
                if ust[cols[a + r]] == d - 1:
                    mg[grp[a + r]] += 1
                key[r] = grp[a + r] * 2.0 + (1.0 - uu[p, a + r])
                mark[r] = False
            o = np.argsort(key[:m], kind='mergesort')
            for q in range(m):
                r = o[q]
                g = grp[a + r]
                if cg[g] < mg[g]:
                    mark[r] = True
                cg[g] += 1
            _sel(p, a, m, K[d], be_day[d], mark, sc, O, U, G)
            for r in range(m):
                if U[p, a + r]:
                    ust[cols[a + r]] = d
    return G


@nb.njit(**NJ)
def _sel(p, a, m, Kd, be, mark, sc, O, U, G):
    """= stable argsort(s − be·mark)[:K]（e6l_fast._select_single 同式的直接版：v = s − be·mark，(v, 位置) 字典序取前 K）。"""
    anym = False
    for r in range(m):
        if mark[r] and be != 0.0:
            anym = True
            break
    if not anym:
        for r in range(m):
            G[p, a + r] = U[p, a + r]
        return
    v = np.empty(m)
    for r in range(m):
        v[r] = sc[p, a + r] - (be if mark[r] else 0.0)
    o = np.argsort(v, kind='mergesort')
    for q in range(Kd):
        G[p, a + o[q]] = True


def rmem_final(form, memory, alpha, kf, paths):
    import e6l_fast as FA
    st, SF = CTX['structs'][form]
    seg = CTX['seg']
    k0 = np.asarray(st.q0, float)
    a = float(alpha)
    P = len(paths)
    Q = np.broadcast_to(np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)[None, :], (P, seg.n))
    SC = np.ascontiguousarray(st.gate_scores(Q))
    O, U = FA.order_U(SC, SF.off, SF.K)
    ids = np.asarray(st.ids, np.int64)
    kind = 'HG' if memory == 'HG10' else 'LAG'
    UU = np.vstack([u_cells(path_key('R_MEMORY', kind, 'GATE_DOMAIN', 'P5', p), ids, 5)[None, :] for p in paths])
    grp = np.zeros(len(ids), np.int64)
    be = np.full(seg.T, 10.0 * st.bunit)
    if kind == 'HG':
        G = FA.rec_rmark(SC, O, U, SF.off, SF.K, SF.cols, be, SF.Nc, grp, np.ascontiguousarray(UU))
    else:
        G = rec_rmark_lag(SC, O, U, SF.off, SF.K, SF.cols, be, SF.Nc, grp, np.ascontiguousarray(UU))
    return SF.down(G)


# ====================================================================== LEGACY（原资格 e随机：对象自身 Q 槽 kf 当日 IID 置换）
def legacy_kf(variant, kf, paths):
    import e6j_fast as FJ
    B = CTX['B']
    V_ = np.isfinite(kf)
    cells = np.flatnonzero(V_)
    asg = FJ.Assigner(kf[V_], B.t[V_].astype(np.int64))
    out = np.repeat(kf[None, :], len(paths), axis=0)
    for i, p in enumerate(paths):
        u = u_cells(path_key('LEGACY_POLICY_RANDOM', 'E6n.' + variant, 'P_production_v2', 'IID', p), cells, 1)
        out[i, V_] = asg(u)
    return out


# ====================================================================== 任务
def claim(mech, gkey, path0, npaths):
    """任务认领（多个父进程共享同一队列时防重复；O_CREAT | O_EXCL 原子创建）。已有 SUCCEEDED 回执或别人已认领 → False。"""
    stem = '%s__p%d_%d' % (gkey.replace('|', '_'), path0, npaths)
    rp = N.P('task_status', 'E6n_rand_%s_%s_%s.receipt.json' % (mech, CTX['seg_name'], stem))
    if os.path.exists(rp):
        try:
            if json.load(open(rp)).get('status') == 'SUCCEEDED':
                return False
        except Exception:                                                     # noqa: BLE001
            pass
    d = N.P('randoms_claims', CTX['seg_name'])
    os.makedirs(d, exist_ok=True)
    try:
        fd = os.open(os.path.join(d, '%s_%s.claim' % (mech, stem)), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, ('%d %s' % (os.getpid(), time.strftime('%F %T'))).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def run_task(args):
    try:
        if len(args) > 7 and args[7] and not claim(args[0], args[1], args[2], args[3]):
            return ('SKIPPED', dict(stem='%s__p%d_%d' % (args[1].replace('|', '_'), args[2], args[3]), mech=args[0]))
        return _run_task(*args[:7])
    except Exception as e:                                                    # noqa: BLE001
        import traceback
        return ('FAILED', '%s: %s\n%s' % (type(e).__name__, e, traceback.format_exc()[-2500:]))


def real_kf(variant, cache):
    if variant not in cache:
        cache[variant] = VR.variant_kf(CTX['B'], variant)[0]
    return cache[variant]


def _run_task(mech, gkey, path0, npaths, rows, out_dir, write):
    from e6l_run_rand import accum_nb
    t0 = time.time()
    seg, AF, B = CTX['seg'], CTX['AF'], CTX['B']
    T = seg.T
    R = pd.DataFrame(rows).sort_values(['form', 'mask_key', 'H']).reset_index(drop=True)
    nr = len(R)
    row_of = {(r.form, r.mask_key, int(r.H)): i for i, r in enumerate(R.itertuples())}
    keys = R.drop_duplicates(['form', 'mask_key'])[['form', 'mask_key', 'memory', 'alpha', 'variant', 'ctrl']].to_dict('records')
    Hs_of = R.groupby(['form', 'mask_key']).H.apply(lambda s: sorted(set(int(h) for h in s))).to_dict()
    s_net = np.zeros((nr, npaths))
    n_net = np.zeros((nr, npaths), np.int32)
    s_gross = np.zeros((nr, npaths))
    n_gross = np.zeros((nr, npaths), np.int32)
    s_turn = np.zeros((nr, npaths))
    s_pos = np.zeros((nr, npaths))
    dsum = np.zeros((nr, T))
    dsq = np.zeros((nr, T))
    dcnt = np.zeros((nr, T), np.int32)
    aud = [p for p in AUDIT_PATHS if path0 <= p < path0 + npaths]
    samp = np.full((nr, len(aud), 4, T), np.nan) if aud else np.zeros((nr, 0, 4, T))
    fp = np.zeros((nr, npaths), np.uint64)
    tim = dict(kf=0.0, gate=0.0, acct=0.0)
    grp = None
    if mech in MECHS_CONTENT:
        vs = set()
        for k in keys:
            v = k['variant']
            if v.startswith('CDOSE'):
                vs.add('|'.join(v.split('|')[1:]))
                vs.add(k['ctrl'])
            else:
                vs.add(v)
        grp = Group(gkey, sorted(vs))
    dlog = []
    rcache = {}
    for b0 in range(0, npaths, BATCH):
        paths = list(range(path0 + b0, path0 + min(npaths, b0 + BATCH)))
        P = len(paths)
        ta = time.time()
        KFs, ACT = {}, {}
        if grp is not None:
            per = []
            for p in paths:
                don, strat = grp.donors(mech, p)
                if p < DONOR_LOG_PATHS:
                    dlog.append((p, donor_log(grp.dom_idx, don, B.t, B.c, strat, T)))
                per.append(grp.kf_path(don, ACT))
            for v in per[0]:
                KFs[v] = np.vstack([x[v][None, :] for x in per])
        tim['kf'] += time.time() - ta
        for k in keys:
            form, mk, mem, alpha, variant, ctrl = k['form'], k['mask_key'], k['memory'], k['alpha'], k['variant'], k['ctrl']
            tg = time.time()
            if mech == 'R_MEMORY':
                F = rmem_final(form, mem, alpha, real_kf(variant, rcache), paths)
            elif mech == 'LEGACY_POLICY_RANDOM':
                kfr = real_kf(variant, rcache) if not variant.startswith('NATIVE') else None
                KL = legacy_kf(variant, kfr, paths)
                F = gate_final(form, mem, alpha, KL, variant, ctrl)
            elif variant.startswith('CDOSE'):
                ov = '|'.join(variant.split('|')[1:])
                F = gate_final(form, mem, alpha, KFs[ov], variant, ctrl, KFC=KFs[ctrl], act=grp.act_real[ov])
            else:
                F = gate_final(form, mem, alpha, KFs[variant], variant, ctrl)
            tim['gate'] += time.time() - tg
            tc = time.time()
            Hs = np.asarray(Hs_of[(form, mk)], np.int64)
            hrow = np.array([row_of[(form, mk, int(h))] for h in Hs], np.int64)
            for i, p in enumerate(paths):
                out, nn = AF.run(F[i], Hs)
                kc = p - path0
                accum_nb(out, hrow, kc, s_net, n_net, s_gross, n_gross, s_turn, s_pos, dsum, dsq, dcnt)
                fp[hrow, kc] = np.frombuffer(hashlib.blake2b(np.packbits(F[i]).tobytes(), digest_size=8).digest(), np.uint64)[0]
                if p in aud:
                    j = aud.index(p)
                    for hi, r in enumerate(hrow):
                        samp[r, j] = (out[hi, 3], out[hi, 0], out[hi, 1], out[hi, 2])
            tim['acct'] += time.time() - tc
    slug = gkey.replace('|', '_')
    od = os.path.join(out_dir, mech, CTX['seg_name'])
    os.makedirs(od, exist_ok=True)
    stem = '%s__p%d_%d' % (slug, path0, npaths)
    pth = os.path.join(od, stem + '.npz')
    N.atomic_write_npz(pth, desc=R.obj.values.astype('U'), H=R.H.values.astype(np.int64), form=R.form.values.astype('U'),
                       mask_key=R.mask_key.values.astype('U'), table=R.table.values.astype('U'), mechanism=np.array([mech], dtype='U'),
                       group=np.array([gkey], dtype='U'), path0=np.array([path0]), n_paths=np.array([npaths]), audit_paths=np.array(aud, np.int64),
                       s_net=s_net, n_net=n_net, s_gross=s_gross, n_gross=n_gross, s_turn=s_turn, s_pos=s_pos, dsum=dsum, dsq=dsq, dcnt=dcnt,
                       samp=samp, fp=fp, dates=np.array([str(d)[:10] for d in seg.dates], dtype='U'),
                       contract_version=np.array([N.CONTRACT_VERSION], dtype='U'))
    outs = [pth]
    if dlog:
        pd_ = os.path.join(od, 'donor_%s.npz' % stem)
        N.atomic_write_npz(pd_, paths=np.array([p for p, _ in dlog], np.int64), log=np.stack([x for _, x in dlog]),
                           cols=np.array(['n_movable', 'moved_share', 'self_share', 'donor_change_rate', 'single_stratum_share'], dtype='U'),
                           dates=np.array([str(d)[:10] for d in seg.dates], dtype='U'))
        outs.append(pd_)
    wall = time.time() - t0
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0
    if write:
        N.write_receipt('E6n_rand_%s_%s_%s' % (mech, CTX['seg_name'], stem), outs, code=[__file__, VR.__file__], rows=nr, n_paths=npaths, path0=path0,
                        wall_s=round(wall, 1), maxrss_gb=round(rss, 2), t_kf=round(tim['kf'], 1), t_gate=round(tim['gate'], 1),
                        t_acct=round(tim['acct'], 1), mismatch=(getattr(grp, 'mismatch', {}) if grp is not None else {}))
    return ('SUCCEEDED', dict(stem=stem, mech=mech, rows=nr, paths=npaths, wall=round(wall, 1), rss=round(rss, 2),
                              t=dict((k, round(v, 1)) for k, v in tim.items())))


# ====================================================================== selftest（不读收益）
def selftest(seg_name, forms, out):
    """① pct_src ≡ 已存测量（km_* / RAW kf 缓存）逐位；② 恒等 donor：整条快管道（pct → 生成 → 门 → 记忆 → 下游）≡ masks/<段>/<形态>.npz 逐格；
    ③ path_key / u 两次调用同序列（A5-1）；④ donor 映射是可动域上的双射、层内（层号守恒）；层 < 2 不动；⑤ LEGACY 置换保当日多重集。"""
    load_ctx(seg_name, forms, acct=False)
    B = CTX['B']
    lm, off = CTX['lm'], CTX['off']
    rows = []
    add = lambda item, obj, ok, detail='': rows.append(dict(segment=seg_name, item=item, object=obj, status='PASS' if ok else 'FAIL', detail=str(detail)[:300]))
    # ①
    for nm in sorted(os.listdir(B.d)):
        if not nm.startswith('km_'):
            continue
        base = nm[3:-4]
        f, dr = base.rsplit('_', 1)
        raw = B.get('raw_' + f)
        ref = B.get(nm[:-4])
        got = pct_src(raw, lm, off, dr)
        same = (np.isfinite(ref) == np.isfinite(got)).all() and (ref[np.isfinite(ref)] == got[np.isfinite(got)]).all()
        add('PCT_SRC_EQ_KM', nm[:-4], same, 'cells=%d' % len(ref))
    M = manifest()
    M = M[M.mechanism == 'CONTENT_IID']
    for gkey, g in M.groupby('group'):
        vs = set()
        for r in g.itertuples():
            if r.variant.startswith('CDOSE'):
                vs.add('|'.join(r.variant.split('|')[1:]))
                vs.add(r.ctrl)
            else:
                vs.add(r.variant)
        grp = Group(gkey, sorted(vs))
        act = {}
        kfi = grp.kf_path(None, act, identity=True)
        for v, kf in kfi.items():
            ref = VR.variant_kf(B, v)[0]
            same = (np.isfinite(ref) == np.isfinite(kf)).all() and (ref[np.isfinite(ref)] == kf[np.isfinite(kf)]).all()
            add('IDENTITY_KF_EQ_DETERMINISTIC', v, same, 'group=%s' % gkey)
        for form in forms:
            z = np.load(N.P('masks', seg_name, '%s.npz' % form), allow_pickle=False)
            mk_all = [str(k) for k in z['mask_keys']]
            n = int(z['n_cells'][0])
            for k in g[g.form == form].drop_duplicates('mask_key').itertuples():
                if k.variant.startswith('CDOSE'):
                    ov = '|'.join(k.variant.split('|')[1:])
                    F = gate_final(form, k.memory, k.alpha, kfi[ov][None, :], k.variant, k.ctrl, KFC=kfi[k.ctrl][None, :], act=grp.act_real[ov])[0]
                else:
                    F = gate_final(form, k.memory, k.alpha, kfi[k.variant][None, :], k.variant, k.ctrl)[0]
                ref = np.unpackbits(z['final_bits'][mk_all.index(k.mask_key)])[:n].astype(bool)
                add('IDENTITY_MASK_EQ_DETERMINISTIC', '%s|%s' % (form, k.mask_key), bool((F == ref).all()), 'diff=%d' % int((F != ref).sum()))
        # ④ donor 双射与层守恒（两机制各一条路径）
        for mech in ('CONTENT_ISK_P5', 'CONTENT_QRANGE_P5', 'CONTENT_IID'):
            don, strat = grp.donors(mech, 0)
            don2, _ = grp.donors(mech, 0)
            di = grp.dom_idx
            bij = np.array_equal(np.sort(don), di)
            pos = np.searchsorted(di, don)
            same_strat = bool((strat[pos] == strat).all())
            _, inv, cnt = np.unique(strat, return_inverse=True, return_counts=True)
            single_fixed = bool((don[cnt[inv] < 2] == di[cnt[inv] < 2]).all())
            add('DONOR_BIJECTION_STRATUM', '%s|%s' % (gkey, mech), bij and same_strat and single_fixed and np.array_equal(don, don2),
                'moved=%.3f single=%.3f' % (float((don != di).mean()), float((cnt[inv] < 2).mean())))
    # ③
    k = path_key('CONTENT_IID', 'X', 'QGOOD|f5', 'IID', 7)
    cells = np.arange(min(1000, B.n))
    add('PATH_KEY_DETERMINISTIC', 'u(key, block, ticker)', np.array_equal(u_cells(k, cells, 5), u_cells(k, cells, 5)), 'key=%d' % k)
    # ⑤
    kf = B.kQ
    L = legacy_kf('Q0', kf, [0, 1])
    okm = True
    for d in range(0, len(off) - 1, 97):
        a, b = off[d], off[d + 1]
        x = np.sort(kf[a:b][np.isfinite(kf[a:b])])
        for i in range(2):
            y = np.sort(L[i, a:b][np.isfinite(L[i, a:b])])
            okm &= np.array_equal(x, y)
    add('LEGACY_MULTISET_PRESERVED', 'Q0', okm)
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    N.atomic_write_csv(out, df)
    return df


# ====================================================================== 父进程
def plan_tasks(M, mechs, path0, npaths, groups=None):
    tasks = []
    for mech in mechs:
        sub = M[M.mechanism == mech]
        for gkey, g in sub.groupby('group'):
            if groups and gkey not in groups:
                continue
            rows = g[['obj', 'form', 'mask_key', 'table', 'H', 'variant', 'ctrl', 'memory', 'alpha']].to_dict('records')
            for q0 in range(path0, path0 + npaths, CHUNK):
                tasks.append((mech, gkey, q0, min(CHUNK, path0 + npaths - q0), rows))
    return tasks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['manifest', 'selftest', 'run'])
    ap.add_argument('--seg', default='')
    ap.add_argument('--mechs', default=','.join(MECHS))
    ap.add_argument('--groups', default='')
    ap.add_argument('--path0', type=int, default=0)
    ap.add_argument('--npaths', type=int, default=FIRST)
    ap.add_argument('--workers', type=int, default=24)
    ap.add_argument('--forms', default=','.join(PARENTS6))
    ap.add_argument('--claim', action='store_true', help='多父进程共享队列：任务先原子认领（randoms_claims/），已认领 / 已成功的跳过')
    a = ap.parse_args()
    if a.step == 'manifest':
        M = manifest()
        p = N.P('registry', 'random_manifest_E6n.csv')
        N.atomic_write_csv(p, M)
        s = M.groupby(['mechanism']).agg(rows=('obj', 'size'), keys=('mask_key', 'nunique'), groups=('group', 'nunique')).reset_index()
        N.write_receipt('E6n_rand_manifest', [p], code=[__file__], **{r.mechanism: dict(rows=int(r.rows), groups=int(r.groups)) for r in s.itertuples()})
        print(s.to_string(index=False))
        return 0
    forms = a.forms.split(',')
    if a.step == 'selftest':
        out = N.P('stage0', 'c5_random', 'selftest_%s.csv' % a.seg)
        df = selftest(a.seg, forms, out)
        N.write_receipt('E6n_rand_selftest_%s' % a.seg, [out], code=[__file__], **df.status.value_counts().to_dict())
        print(df.groupby(['item', 'status']).size().to_string())
        return 0 if (df.status == 'PASS').all() else 2
    import e6n_gate as GT
    if a.seg in N.POST_SEGS:
        GT.post_gate(a.seg, 'randoms %s' % a.seg)
    else:
        GT.deriv_ready(a.seg, 'randoms %s' % a.seg)
    M = pd.read_csv(N.P('registry', 'random_manifest_E6n.csv'), keep_default_na=False)
    M = M[M.form.isin(forms)]
    tasks = plan_tasks(M, a.mechs.split(','), a.path0, a.npaths, set(a.groups.split(',')) if a.groups else None)
    done = set()
    for t in tasks:
        stem = '%s__p%d_%d' % (t[1].replace('|', '_'), t[2], t[3])
        rp = N.P('task_status', 'E6n_rand_%s_%s_%s.receipt.json' % (t[0], a.seg, stem))
        if os.path.exists(rp) and json.load(open(rp)).get('status') == 'SUCCEEDED':
            done.add((t[0], t[1], t[2], t[3]))
    tasks = [t for t in tasks if (t[0], t[1], t[2], t[3]) not in done]
    print('%s：%d 个任务（已完成跳过 %d）' % (a.seg, len(tasks), len(done)), flush=True)
    load_ctx(a.seg, forms)
    print('环境 %.0fs；maxrss %.1f GB' % (CTX['t_env'], resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576.0), flush=True)
    order = sorted(range(len(tasks)), key=lambda i: -len(tasks[i][4]) * tasks[i][3])
    jobs = [tasks[i] + (N.P('randoms'), True, a.claim) for i in order]
    ctx = mp.get_context('fork')
    bad = 0
    t0 = time.time()
    with ctx.Pool(a.workers, maxtasksperchild=8) as pool:
        for st, info in pool.imap_unordered(run_task, jobs):
            if st == 'SKIPPED':
                continue
            if st != 'SUCCEEDED':
                bad += 1
                print('FAILED', N.san(str(info)), flush=True)
            else:
                print('done %s %s rows %d paths %d wall %.0fs rss %.1fGB %s' % (info['mech'], info['stem'], info['rows'], info['paths'], info['wall'],
                                                                             info['rss'], info['t']), flush=True)
    print('ALL_DONE %s bad=%d wall %.0fs' % (a.seg, bad, time.time() - t0), flush=True)
    return 0 if bad == 0 else 2


if __name__ == '__main__':
    sys.exit(main())
