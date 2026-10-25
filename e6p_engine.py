# -*- coding: utf-8 -*-
"""E6p 账户引擎 = E6o 现金引擎（e6o_engine，NATIVE lag1 RESET_H ALLOW 原实现逐式保留）+ 本轮受控扩展（plan §5–§9；brief §1.3 / §3）。
所有扩展由参数开关控制，全关时浮点运算序列与 E6o 相同（S0-2 E6O_ACCOUNT_REPLICATION / S0-3 零干预恒等逐位核）。
扩展：
- 部署（plan §6.2 / §6.5）：TARGET（D80 / D95）与 MIRROR（目标 = owner 在 T 收盘已观测敞口）只买不强卖；T 收盘在常规批次与 NATIVE 额外批次计划之后，
  K_T = min{max(0, 目标·NAV_T − 计划风险值), 普通现金扣计划买入与费用预留, 余量容量}；按当日源形成名单 ∝ 源权重做两层（单股 / 行业）带上限水位分配；
  部署买入只用普通现金；成交缩放先缩部署（zd）、再额外（zx）、再常规（zr）。上限 profile：SOURCE（单股 1% NAV、行业 clean 份额 + 3pp）/
  RELATIVE_UPPER（单股 1 / N_clean + 1pp、行业份额 + 3pp）/ ABS01（单股 1%、行业份额 + 3pp）；含全部已有批次（plan §6.3）。
- RENEW5（plan §5.2）：执行检查点 e = e0 + 5m < due，前一收盘查无记忆自然名单（memory = NONE 的源形成名单）：已知不含 → e 日卖（kind RENEW）；
  名单为空（段首预热）或本股当日未开盘 = UNKNOWN，不新增卖单；due 不变。
- 再投资三臂（plan §6.6）：HALF：早退净款 η 进标签（lag1、到原 due 重分类）、1 − η 锁到原 due（累计额度 ηF，不是每日减半）；
  COST0 / COSTNET：NATIVE 额外批次的分配换成固定预算凸成本路由（成本未知 / 退化名字冻结原分配），并逐日记同快照 native / cost0 / costnet 局部成本。
- 成本系数（plan §9.2）：S_δ = Σ_i (dn_i / V⁺_{e−1}) σ_i √p0 (dn_i / (V0 · ADV_i · p0))^δ，δ ∈ {.5, .7}；固定路径成本份额 = κ A^δ S_δ。
- 反馈账户（plan §9.4）：冲击费 κ σ √p0 (dn A / (V0 ADV p0))^δ × dn 实扣现金。
- 随机 V2（plan §8）：AMOUNT_MATCH_V2 / LEVEL_WORST_1D（两级：日龄桶内 → 本路径全部 R_INTENT 回填）、COUNT_ISK（行业 × size 三档 × 日龄桶，依次回填）、
  AMOUNT_ISK_V2（同层金额 → 全域回填）、R_CHECKPOINT（检查点批次内取消同金额持有许可）；每日记 requested / within / cross / unmatched。
- 成交日志逐批次（B.18）、批次关闭日龄直方、证券连续持有日龄、行业主动偏离日最大值。"""
import numpy as np
from numba import njit

IP_H, IP_TRIG, IP_SEL, IP_FUND, IP_LAG, IP_MAT, IP_RE, IP_GUARD, IP_EXIT, IP_IDEAL, IP_RECON, IP_SEED, IP_SHADOW, IP_NLAYER, IP_TLOG = range(15)
IP_DEPLOY, IP_CAP, IP_RENEW, IP_RECYCLE, IP_FEEDBACK, IP_ZEROK, IP_RENEWOK = range(15, 22)
NIP = 24
FP_V0, FP_FEE, FP_SCAP, FP_IDEV, FP_T2, FP_T6A, FP_T6B, FP_T1C, FP_T1D = range(9)
FP_TARGET, FP_ETA, FP_RA, FP_RK, FP_RD, FP_P0, FP_FBA, FP_FBK, FP_FBD = range(9, 18)
NFP = 20
TM_NONE, TM_PANEL, TM_T1C, TM_T1D, TM_T2, TM_T2P, TM_T6A, TM_T6B, TM_ALLFIRST = range(9)
SM_REAL, SM_AMOUNT, SM_COUNT, SM_ISK, SM_LEVEL, SM_BERN, SM_REELIG, SM_AMT2, SM_ISK2, SM_LVL2, SM_AISK2, SM_RCHK = range(12)
FD_NATIVE, FD_CASH, FD_NEXT, FD_NONE = range(4)
RE_ALLOW, RE_BLOCK, RE_RECONFIRM = range(3)
GD_OFF, GD_T1A, GD_LVL, GD_RANDOM = range(4)
RC_NONE, RC_T1A, RC_LVL = range(3)
DP_NONE, DP_TARGET, DP_MIRROR = range(3)
CP_SOURCE, CP_REL, CP_ABS01 = range(3)
RY_NONE, RY_HALF, RY_COST0, RY_COSTNET = range(4)
NB = 6                                   # V2 日龄桶：1 / 2 / 3–5 / 6–10 / 11–20 / 21+
KD_TRIG, KD_RENEW, KD_RAND, KD_RCHK = range(4)
OK_REGULAR, OK_EXIT, OK_EXTRA, OK_RENEW, OK_DUE = range(5)
DY_COLS = ('nav_pre', 'nav_post', 'fee', 'exposure', 'bench', 'net_excess', 'cash_share', 'n_hold', 'n_exits', 'r_net',
           'traded', 'impact_br', 'qmiss', 'sz_num', 'sz_den', 'sz_unk', 'tag_amt', 'nav_close', 'n_intents', 'x_prev',
           'n_internal', 'buy_val', 'sell_val', 'cancel_val', 'unmatched_val', 'stale_val', 'lock_amt', 'early_val',
           'zr', 'zx', 'tag_use_reg', 'tag_use_ext', 'extra_plan', 'n_risk', 'tag_new', 'tag_matured', 'lock_new', 'lock_matured', 'n_reentry',
           'cost_s05', 'cost_s07', 'deploy_plan', 'deploy_buy', 'renew_n', 'zd', 'full_bench_ex', 'target_expo', 'n_lots', 'fb_impact',
           'v2_req', 'v2_within', 'v2_cross', 'v2_unm', 'v2_nreq', 'v2_nunm', 'rt_budget', 'rt_native', 'rt_cost0', 'rt_costnet', 'rt_unknown',
           'rt_degen', 'sector_active_max', 'sec_age_sum', 'sec_age_n', 'extra_val', 'renew_exec', 'lots_closed', 'lots_closed_due', 'noact',
           'deploy_cap_used', 'n_checkpoints', 'n_confirmed', 'n_rejected', 'n_unknown', 'early_exec_n', 'renew_qmiss')
NDY = len(DY_COLS)
DYI = {k: i for i, k in enumerate(DY_COLS)}
SF_CASH, SF_VPREV, SF_XPREV, SF_LOCKDAYS = range(4)
NSF = 8
SI_NL, SI_NEXTID, SI_NTK, SI_NLK, SI_NPB, SI_NIN, SI_NTKID, SI_ERR, SI_INTERNAL, SI_REBLK, SI_RECONF, SI_REENTRY, SI_UNKDAYS, SI_NTL = range(14)
SI_LCLOSED, SI_LDUE, SI_NOACT, SI_RCHK, SI_RCONF2, SI_RREJ, SI_RUNK, SI_RNDFIX = range(14, 22)
NSI = 24
IN_DAY, IN_SEC, IN_LAYER, IN_EXEC, IN_STATUS, IN_ISK, IN_RE, IN_LOT, IN_KIND, IN_AGE, IN_DUE, IN_LID = range(12)
NIN_I = 12
LQ_NONE, LQ_EARLY, LQ_DUE = 0, 1, 2
# L_i 列：0 sec, 1 e0, 2 due, 3 req, 4 reqday, 5 extra（0 常规 / 1 额外 / 2 额外按段 / 3 部署）, 6 intent row, 7 alive
# L_f 列：0 qty, 1 entry px, 2 entry close cvr, 3 sigma pre-entry
# TL_i 列：0 day, 1 sec, 2 lot_id, 3 request row, 4 order_kind, 5 side（0 买 / 1 卖）, 6 lot_due；TL_f 列：0 qty, 1 notional, 2 price, 3 fee


@njit(cache=True)
def hash_u(seed, d, i):
    x = np.uint64(seed) ^ (np.uint64(d) * np.uint64(0x9E3779B97F4A7C15)) ^ (np.uint64(i + 1) * np.uint64(0xD1B54A32D192ED03))
    x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
    x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
    x = x ^ (x >> np.uint64(31))
    return float(x >> np.uint64(11)) * (1.0 / 9007199254740992.0)


@njit(cache=True)
def in_csr(ptr, col, d, s):
    a, b = ptr[d], ptr[d + 1]
    lo, hi = a, b
    while lo < hi:
        m = (lo + hi) // 2
        if col[m] < s:
            lo = m + 1
        else:
            hi = m
    return lo < b and col[lo] == s


@njit(cache=True)
def bucket_of(age):
    if age <= 1:
        return 0
    if age == 2:
        return 1
    if age <= 5:
        return 2
    if age <= 10:
        return 3
    if age <= 20:
        return 4
    return 5


@njit(cache=True)
def new_lot(L_i, L_f, L_id, S_i, sec, e0, due, px, sig, extra, qty):
    n = S_i[SI_NL]
    if n >= L_i.shape[0]:
        S_i[SI_ERR] = 1
        return -1
    L_i[n, 0] = sec
    L_i[n, 1] = e0
    L_i[n, 2] = due
    L_i[n, 3] = LQ_NONE
    L_i[n, 4] = -1
    L_i[n, 5] = extra
    L_i[n, 6] = -1
    L_i[n, 7] = 1
    L_f[n, 0] = qty
    L_f[n, 1] = px
    L_f[n, 2] = np.nan
    L_f[n, 3] = sig
    L_id[n] = S_i[SI_NEXTID]
    S_i[SI_NEXTID] += 1
    S_i[SI_NL] = n + 1
    return n


@njit(cache=True)
def compact_lots(L_i, L_f, L_id, IN_i, S_i):
    n = S_i[SI_NL]
    k = 0
    for j in range(n):
        if L_i[j, 7] == 1:
            if k != j:
                for cc in range(L_i.shape[1]):
                    L_i[k, cc] = L_i[j, cc]
                for cc in range(L_f.shape[1]):
                    L_f[k, cc] = L_f[j, cc]
                L_id[k] = L_id[j]
                if L_i[k, 6] >= 0:
                    IN_i[L_i[k, 6], IN_LOT] = k
            k += 1
    S_i[SI_NL] = k


@njit(cache=True)
def tk_add(TK_f, TK_i, S_i, amt, unlock, due, nslot):
    """标签 / 锁定：全生命周期 ID 只增不减（到期删除后同 ID 不可再生）。"""
    n = S_i[nslot]
    if n >= TK_f.shape[0]:
        S_i[SI_ERR] = 2
        return -1
    if not np.isfinite(amt) or amt < 0.0 or unlock > due:
        S_i[SI_ERR] = 3
        return -1
    TK_f[n] = amt
    TK_i[n, 0] = unlock
    TK_i[n, 1] = due
    TK_i[n, 2] = 1
    TK_i[n, 3] = S_i[SI_NTKID]
    S_i[SI_NTKID] += 1
    S_i[nslot] = n + 1
    return n


@njit(cache=True)
def tk_compact(TK_f, TK_i, S_i, nslot):
    n = S_i[nslot]
    k = 0
    for j in range(n):
        if TK_i[j, 2] == 1 and TK_f[j] > 1e-12:
            if k != j:
                TK_f[k] = TK_f[j]
                for cc in range(4):
                    TK_i[k, cc] = TK_i[j, cc]
            k += 1
    S_i[nslot] = k


@njit(cache=True)
def tk_sum(TK_f, TK_i, n, day, usable_only):
    s = 0.0
    for j in range(n):
        if TK_i[j, 2] == 1:
            if usable_only:
                if TK_i[j, 0] <= day and day < TK_i[j, 1]:
                    s += TK_f[j]
            else:
                s += TK_f[j]
    return s


@njit(cache=True)
def tk_consume(TK_f, TK_i, n, day, amount, out_due, out_amt):
    """按 due 最早、ID 序消耗可用标签；返回段数（填 out_due / out_amt）。超额 / 非有限 → −1（双花拦截）。"""
    avail = tk_sum(TK_f, TK_i, n, day, True)
    if not np.isfinite(amount) or amount < 0.0 or amount > avail * (1.0 + 1e-12) + 1e-9:
        return -1
    k = 0
    left = min(amount, avail)
    while left > 1e-12:
        best = -1
        for j in range(n):
            if TK_i[j, 2] == 1 and TK_i[j, 0] <= day and day < TK_i[j, 1] and TK_f[j] > 1e-15:
                if best < 0 or TK_i[j, 1] < TK_i[best, 1] or (TK_i[j, 1] == TK_i[best, 1] and TK_i[j, 3] < TK_i[best, 3]):
                    best = j
        if best < 0:
            break
        v = min(left, TK_f[best])
        TK_f[best] -= v
        left -= v
        if k < out_due.shape[0]:
            out_due[k] = TK_i[best, 1]
            out_amt[k] = v
            k += 1
    return k


@njit(cache=True)
def mid_rank(vals):
    n = len(vals)
    o = np.argsort(vals)
    r = np.empty(n)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and vals[o[j + 1]] == vals[o[i]]:
            j += 1
        mid = (i + 0.5 * (j - i + 1)) / n
        for k in range(i, j + 1):
            r[o[k]] = mid
        i = j + 1
    return r


@njit(cache=True)
def exec_qty(s, d, zr, zx, zd, P, Sreq, Br, Bx, Bd, isopen, sellable, buyable, ideal):
    """单证券当日成交量（买 / 卖股数）：内部转移先做，净额看方向可行性。部署类 Bd 恒为 0 时与 E6o 同式。"""
    bq = (zr * Br + zx * Bx + zd * Bd) / P
    sq = Sreq
    if ideal:
        return bq, sq
    if not isopen[d, s]:
        return 0.0, 0.0
    cs = sellable[d, s]
    cb = buyable[d, s]
    if not cs:
        sq = min(Sreq, bq)
    if not cb:
        bq = min(bq, sq)
    return bq, sq


@njit(cache=True)
def fb_cost(dn, sg, av, fbA, fbK, fbD, p0, V0):
    """反馈账户冲击费（内部单位）：dn · κσ√p0 (dn·A / (V0·ADV·p0))^δ；σ / ADV 缺失 → 0（计 qmiss）。"""
    if not (dn > 0.0) or not np.isfinite(sg) or not np.isfinite(av) or av <= 0.0:
        return 0.0
    return dn * fbK * sg * np.sqrt(p0) * (dn * fbA / (V0 * av * p0)) ** fbD


@njit(cache=True)
def solve_eval(d, zr, zx, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
               fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0):
    """返回 (S_tot, S_early, R_buy, X_buy, D_buy, F)。早退卖款按证券内早退请求占比分摊（DUE 先卖）。"""
    S_tot = 0.0
    S_early = 0.0
    R_buy = 0.0
    X_buy = 0.0
    D_buy = 0.0
    net_abs = 0.0
    fimp = 0.0
    for k in range(nt):
        s = tlist[k]
        P = pv[d, s]
        if not (P > 0.0):
            continue
        bq, sq = exec_qty(s, d, zr, zx, zd, P, S_req[s], B_r[s], B_x[s], B_d[s], isopen, sellable, buyable, ideal)
        S_tot += sq * P
        due_part = S_req[s] - S_early_req[s]
        S_early += max(0.0, sq - due_part) * P
        tot = zr * B_r[s] + zx * B_x[s] + zd * B_d[s]
        if tot > 0.0:
            fr = zr * B_r[s] / tot
            fd = zd * B_d[s] / tot
            R_buy += bq * P * fr
            D_buy += bq * P * fd
            fx = 1.0 - fr - fd                     # 常规 + 部署份额舍入可略超 1：额外份额取非负（部署为零时 fx = 1 − fr ≥ 0，与 E6o 同式）
            X_buy += bq * P * (fx if fx > 0.0 else 0.0)
        dn = abs(bq - sq) * P
        net_abs += dn
        if fb_on:
            fimp += fb_cost(dn, sig20[d, s], adv20[d, s], fbA, fbK, fbD, p0, V0)
    return S_tot, S_early, R_buy, X_buy, D_buy, c * net_abs + fimp


@njit(cache=True)
def feasible(S_tot, S_early, R_buy, X_buy, D_buy, F, ordinary0, tk_usable, fund, lag, fsh_early):
    """普通现金付常规买入、部署买入与全部费用；常规缺口与额外买入只能用可用标签（lag0 另含当日早退新标签）；部署不碰标签。"""
    E_new = S_early - fsh_early
    S_norm = S_tot - S_early
    need_tag = R_buy + F - fsh_early - S_norm - ordinary0
    if need_tag < 0.0:
        need_tag = 0.0
    if D_buy > 0.0:
        left = ordinary0 + S_norm + fsh_early - R_buy - F
        if left < 0.0:
            left = 0.0
        if D_buy > left + 1e-9:
            return False, need_tag
    if fund == FD_CASH or fund == FD_NONE:
        return need_tag <= 1e-9 and X_buy <= 1e-12, need_tag
    usable = tk_usable + (E_new if lag == 0 else 0.0)
    return need_tag + X_buy <= usable + 1e-9, need_tag


@njit(cache=True)
def prop_capped(p, c, budget):
    """无收益目标：按优先比例 p、单项上限 c 分配预算（plan 附录 C proportional_capped 同式；二分 100 次）。"""
    n = len(p)
    out = np.zeros(n)
    scale = 0.0
    for i in range(n):
        if p[i] > scale:
            scale = p[i]
    pp = np.zeros(n)
    if scale > 0.0:
        for i in range(n):
            pp[i] = p[i] / scale
    cap = 0.0
    for i in range(n):
        if pp[i] > 0.0:
            cap += c[i]
    b = budget if budget < cap else cap
    if not (b > 0.0):
        return out
    hi = 1.0
    while True:
        s = 0.0
        for i in range(n):
            s += min(c[i], hi * pp[i])
        if s >= b - 1e-14:
            break
        hi *= 2.0
        if not np.isfinite(hi):
            return out
    lo = 0.0
    for it in range(100):
        mid = 0.5 * (lo + hi)
        s = 0.0
        for i in range(n):
            s += min(c[i], mid * pp[i])
        if s < b:
            lo = mid
        else:
            hi = mid
    for i in range(n):
        out[i] = min(c[i], hi * pp[i])
    return out


@njit(cache=True)
def alloc2(p, c, grp, gcap, budget):
    """两层只买分配（附录 C allocate）：每组先按组余量饱和成形，再在共同尺度下按比例分预算；grp < 0 = 无行业约束（自成一组、组上限 = 单项上限和）。"""
    n = len(p)
    sat = np.zeros(n)
    done = np.zeros(n, np.bool_)
    for i in range(n):
        if done[i]:
            continue
        g = grp[i]
        cnt = 0
        for k in range(i, n):
            if not done[k] and grp[k] == g:
                cnt += 1
        idx = np.empty(cnt, np.int64)
        m = 0
        for k in range(i, n):
            if not done[k] and grp[k] == g:
                idx[m] = k
                m += 1
                done[k] = True
        pg = np.empty(cnt)
        cg = np.empty(cnt)
        csum = 0.0
        for m in range(cnt):
            pg[m] = p[idx[m]]
            cg[m] = c[idx[m]]
            csum += cg[m]
        gc = gcap[i] if g >= 0 else csum
        a = prop_capped(pg, cg, gc)
        for m in range(cnt):
            sat[idx[m]] = a[m]
    return prop_capped(p, sat, budget)


@njit(cache=True)
def route_x(lam, b, a, u, c, dl):
    n = len(b)
    x = np.zeros(n)
    for i in range(n):
        if abs(lam) <= c:
            y = 0.0
        else:
            y = ((abs(lam) - c) / ((1.0 + dl) * a[i])) ** (1.0 / dl)
            if lam < 0.0:
                y = -y
        v = y - b[i]
        if v < 0.0:
            v = 0.0
        if v > u[i]:
            v = u[i]
        x[i] = v
    return x


@njit(cache=True)
def route_solve1(b, a, u, target, c, dl):
    """min Σ C_i(b_i + x_i)，0 ≤ x ≤ u，Σx = target（附录 C signed_allocate.solve 同式；二分 160 次）。"""
    n = len(b)
    su = 0.0
    for i in range(n):
        su += u[i]
    t = target if target < su else su
    if n == 0 or not (t > 0.0):
        return np.zeros(n)
    lo = 1e300
    hi = -1e300
    for i in range(n):
        q = b[i]
        dv = 0.0 if q == 0.0 else (c + (1.0 + dl) * a[i] * abs(q) ** dl) * (1.0 if q > 0 else -1.0)
        if dv < lo:
            lo = dv
        q = b[i] + u[i]
        dv = 0.0 if q == 0.0 else (c + (1.0 + dl) * a[i] * abs(q) ** dl) * (1.0 if q > 0 else -1.0)
        if dv > hi:
            hi = dv
    lo -= 1.0
    hi += 1.0
    for it in range(160):
        mid = 0.5 * (lo + hi)
        x = route_x(mid, b, a, u, c, dl)
        s = 0.0
        for i in range(n):
            s += x[i]
        if s < t:
            lo = mid
        else:
            hi = mid
    return route_x(0.5 * (lo + hi), b, a, u, c, dl)


@njit(cache=True)
def route_solve(b, a, u, grp, gcap, target, c, dl):
    """两层：组内先按组余量求饱和形状，再全局按目标求解（附录 C signed_allocate）。"""
    n = len(b)
    sat = np.zeros(n)
    done = np.zeros(n, np.bool_)
    for i in range(n):
        if done[i]:
            continue
        g = grp[i]
        cnt = 0
        for k in range(i, n):
            if not done[k] and grp[k] == g:
                cnt += 1
        idx = np.empty(cnt, np.int64)
        m = 0
        for k in range(i, n):
            if not done[k] and grp[k] == g:
                idx[m] = k
                m += 1
                done[k] = True
        bg = np.empty(cnt)
        ag = np.empty(cnt)
        ug = np.empty(cnt)
        usum = 0.0
        for m in range(cnt):
            bg[m] = b[idx[m]]
            ag[m] = a[idx[m]]
            ug[m] = u[idx[m]]
            usum += ug[m]
        gc = gcap[i] if g >= 0 else usum
        xg = route_solve1(bg, ag, ug, gc, c, dl)
        for m in range(cnt):
            sat[idx[m]] = xg[m]
    return route_solve1(b, a, sat, target, c, dl)


@njit(cache=True)
def res_cost(q, a, c, dl):
    return c * abs(q) + a * abs(q) ** (1.0 + dl)


@njit(cache=True)
def tl_add(TL_i, TL_f, S_i, d, s, lot_id, req, kind, side, qty, P, due):
    r = S_i[SI_NTL]
    if r >= TL_i.shape[0]:
        S_i[SI_ERR] = 11
        return
    TL_i[r, 0] = d
    TL_i[r, 1] = s
    TL_i[r, 2] = lot_id
    TL_i[r, 3] = req
    TL_i[r, 4] = kind
    TL_i[r, 5] = side
    TL_i[r, 6] = due
    TL_f[r, 0] = qty
    TL_f[r, 1] = qty * P
    TL_f[r, 2] = P
    TL_f[r, 3] = 0.0
    S_i[SI_NTL] = r + 1


@njit(cache=True)
def mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind):
    s = L_i[j, 0]
    L_i[j, 3] = LQ_EARLY
    L_i[j, 4] = d + 1
    r = S_i[SI_NIN]
    if r < IN_i.shape[0]:
        IN_i[r, IN_DAY] = d
        IN_i[r, IN_SEC] = s
        IN_i[r, IN_LAYER] = lay
        IN_i[r, IN_EXEC] = -1
        IN_i[r, IN_STATUS] = 0
        IN_i[r, IN_ISK] = iskid[d, s]
        bad = (recon == RC_T1A and t1a[d, s] == 1) or (recon == RC_LVL and lvl[d, s] == 1)
        IN_i[r, IN_RE] = (2 if bad else 0) + (1 if in_csr(u_ptr, u_col, d, s) else 0)
        IN_i[r, IN_LOT] = j
        IN_i[r, IN_KIND] = kind
        IN_i[r, IN_AGE] = d + 1 - L_i[j, 1]
        IN_i[r, IN_DUE] = L_i[j, 2]
        IN_i[r, IN_LID] = L_id[j]
        IN_f[r, 0] = L_f[j, 0] * pc[d, s]
        IN_f[r, 1] = L_f[j, 0]
        L_i[j, 6] = r
        S_i[SI_NIN] = r + 1
    else:
        S_i[SI_ERR] = 8
    sec_new_int[s] = True
    if L_i[j, 2] > sec_due_max[s]:
        sec_due_max[s] = L_i[j, 2]
    return 1


@njit(cache=True)
def solve_all(d, zr0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0,
              ordinary0, tk_av, fund, lag):
    """现金约束求解：全额可行则 (1,1,1)；否则先缩部署 zd；部署归零仍不可行 → E6o 原流程（先缩额外 zx，再缩常规 zr；zd 固定）。部署为零时与 E6o 同序同式。"""
    zr = 1.0
    zx = 1.0
    zd = 1.0
    S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, zr, zx, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                              fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
    den = S_tot + R_b + X_b + D_b
    ok, need_tag = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
    err = 0
    if not ok:
        done = False
        if D_b > 0.0:
            S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, 1.0, 1.0, 0.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable,
                                                      ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
            den = S_tot + R_b + X_b + D_b
            okd, nd0 = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
            if okd:
                lo, hi = 0.0, 1.0
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, 1.0, 1.0, mid, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                              buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zd = lo
                done = True
            else:
                zd = 0.0
        if not done:
            lo, hi = 0.0, 1.0
            zx = 0.0
            S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, 1.0, 0.0, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable,
                                                      ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
            den = S_tot + R_b + X_b + D_b
            ok0, need0 = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
            if ok0:
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, 1.0, mid, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                              buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr, zx = 1.0, lo
            else:
                zx = 0.0
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, mid, 0.0, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                              buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr = lo
        S_tot, S_e, R_b, X_b, D_b, F = solve_eval(d, zr, zx, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                                  fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0)
        den = S_tot + R_b + X_b + D_b
        ok, need_tag = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
        if not ok:
            # 缺口 ≤ 1e−6 元 = 普通现金在 0 附近的浮点残差（部署 / 缩量把现金压到 0 后的次日无卖出日），不当不可行（码 12，计数）；E6o 账户从未进入本分支
            err = 9 if need_tag > 1e-6 else 12
    return zr, zx, zd, need_tag, err


@njit(cache=True)
def step(d0, d1, ip, fp,
         pv, pc, pcobs, cvr, cpct, trig, t1a, lvl, sellable, buyable, isopen, sig20, adv20, zsz, ind, capsh, bench, pvage, iskid,
         nclean, tgt_expo,
         f_ptr, f_col, f_w, u_ptr, u_col, n_ptr, n_col, nf_ptr, nf_col,
         tg_amt, tg_cnt, tg_isk, tg_re, p_bern, tg_cancel, tg_b, tg_isk2, tg_aisk, tg_rchk,
         L_i, L_f, L_id, q, ep_until, ep_clear, last_exit_due, first_held,
         TK_f, TK_i, LK_f, LK_i, PB_i, PB_f, S_f, S_i, IN_i, IN_f, DY, HOLDH, LOTH, RISK, HITS, TL_i, TL_f):
    T, N = pv.shape
    tlog = ip[IP_TLOG] == 1
    H = ip[IP_H]
    tmode = ip[IP_TRIG]
    smode = ip[IP_SEL]
    fund = ip[IP_FUND]
    lag = ip[IP_LAG]
    remain = ip[IP_MAT] == 1
    remode = ip[IP_RE]
    guard = ip[IP_GUARD]
    exit_on = ip[IP_EXIT] == 1
    ideal = ip[IP_IDEAL] == 1
    recon = ip[IP_RECON]
    seed = ip[IP_SEED]
    shadow = ip[IP_SHADOW] == 1
    NL = ip[IP_NLAYER]
    dmode = ip[IP_DEPLOY]
    cmode = ip[IP_CAP]
    renew = ip[IP_RENEW]
    rmode = ip[IP_RECYCLE]
    fb_on = ip[IP_FEEDBACK] == 1
    zerok = ip[IP_ZEROK] == 1
    renewok = ip[IP_RENEWOK] == 1
    c = fp[FP_FEE]
    scap = fp[FP_SCAP]
    idev = fp[FP_IDEV]
    V0 = fp[FP_V0]
    tgtc = fp[FP_TARGET]
    eta = fp[FP_ETA]
    rA = fp[FP_RA]
    rK = fp[FP_RK]
    rD = fp[FP_RD]
    p0 = fp[FP_P0]
    fbA = fp[FP_FBA]
    fbK = fp[FP_FBK]
    fbD = fp[FP_FBD]
    sp0 = np.sqrt(p0) if p0 > 0.0 else 0.0
    G = capsh.shape[1]
    S_req = np.zeros(N)
    S_early_req = np.zeros(N)
    B_r = np.zeros(N)
    B_x = np.zeros(N)
    B_d = np.zeros(N)
    touched = np.zeros(N, np.bool_)
    tlist = np.empty(N, np.int64)
    head = np.full(N, -1, np.int64)
    expv = np.zeros(N)
    rankv = np.full(N, -1.0)
    held_mark = np.zeros(N, np.bool_)
    held2 = np.zeros(N, np.bool_)
    seg_due = np.zeros(256, np.int64)
    seg_amt = np.zeros(256)
    indsum = np.zeros(G)
    newsum = np.zeros(G)
    indval = np.zeros(G)
    sec_new_int = np.zeros(N, np.bool_)
    sec_due_max = np.full(N, -1, np.int64)
    leg_due = np.zeros(4096, np.int64)
    leg_val = np.zeros(4096)
    sellv = np.zeros(N)
    for d in range(d0, d1):
        # ================= 执行（VWAP_d）
        mat_tk = 0.0
        mat_lk = 0.0
        for j in range(S_i[SI_NTK]):
            if TK_i[j, 2] == 1 and TK_i[j, 1] <= d:
                TK_i[j, 2] = 0                         # 到原 due：重分类为普通现金（现金不变）
                mat_tk += TK_f[j]
        for j in range(S_i[SI_NLK]):
            if LK_i[j, 2] == 1 and LK_i[j, 1] <= d:
                LK_i[j, 2] = 0
                mat_lk += LK_f[j]
        DY[d, 35] = mat_tk
        DY[d, 37] = mat_lk
        tk_compact(TK_f, TK_i, S_i, SI_NTK)
        tk_compact(LK_f, LK_i, S_i, SI_NLK)
        cash0 = S_f[SF_CASH]
        Vprev0 = S_f[SF_VPREV]
        nl = S_i[SI_NL]
        nxt = np.full(nl, -1, np.int64)
        nt = 0
        V_pre = cash0
        for j in range(nl):
            if L_i[j, 7] != 1:
                continue
            s = L_i[j, 0]
            V_pre += L_f[j, 0] * pv[d, s]
            if L_i[j, 3] == LQ_NONE and L_i[j, 2] <= d:
                L_i[j, 3] = LQ_DUE
                L_i[j, 4] = d
            if L_i[j, 3] != LQ_NONE and L_i[j, 4] <= d and L_f[j, 0] > 0.0:
                S_req[s] += L_f[j, 0]
                if L_i[j, 3] == LQ_EARLY and d < L_i[j, 2]:      # 只算仍早于原 due 的早退（迟到成交不生标签）
                    S_early_req[s] += L_f[j, 0]
                nxt[j] = head[s]
                head[s] = j
                if not touched[s]:
                    touched[s] = True
                    tlist[nt] = s
                    nt += 1
        for k in range(S_i[SI_NPB]):
            s = PB_i[k, 0]
            if PB_i[k, 1] == 0:
                B_r[s] += PB_f[k]
            elif PB_i[k, 1] == 1:
                B_x[s] += PB_f[k]
            else:
                B_d[s] += PB_f[k]
            if not touched[s]:
                touched[s] = True
                tlist[nt] = s
                nt += 1
        # lag0：当日可实现的早退款同清算可用 → 额外买（昨日收盘形成名单形状）
        if exit_on and lag == 0 and fund == FD_NATIVE and d >= 1:
            e_est = 0.0
            for k in range(nt):
                s = tlist[k]
                P = pv[d, s]
                if P > 0.0 and S_early_req[s] > 0.0 and (ideal or (isopen[d, s] and sellable[d, s])):
                    e_est += S_early_req[s] * P
            if e_est > 0.0:
                cap_s = scap * S_f[SF_VPREV]
                for k2 in range(f_ptr[d - 1], f_ptr[d]):
                    s = f_col[k2]
                    add = e_est * f_w[k2]
                    if add <= 0.0:
                        continue
                    if remode != RE_ALLOW and ep_until[s] > d and ep_clear[s] == 0:
                        continue
                    add = min(add, max(0.0, cap_s - B_r[s] - B_x[s]))
                    if add <= 0.0:
                        continue
                    B_x[s] += add
                    if not touched[s]:
                        touched[s] = True
                        tlist[nt] = s
                        nt += 1
        tk_av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
        tag_all = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, False)
        lk_all = tk_sum(LK_f, LK_i, S_i[SI_NLK], d, False)
        ordinary0 = cash0 - tag_all - lk_all
        zr, zx, zd, need_tag, err9 = solve_all(d, 1.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                               fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, ordinary0, tk_av, fund, lag)
        S_f[4] = need_tag                              # 诊断槽（不参与运算）：当日求解后的标签缺口、普通现金、可用标签、不可行标志
        S_f[5] = ordinary0
        S_f[6] = tk_av
        S_f[7] = err9
        if err9 == 9:
            S_i[SI_ERR] = 9                            # 连强制卖出与费用都付不起（不注资，标记）
        elif err9 == 12:
            S_i[SI_RNDFIX] += 1
        n_leg = 0
        net_abs = 0.0
        imp = 0.0
        qmiss = 0.0
        s05 = 0.0
        s07 = 0.0
        fimp = 0.0
        n_int = 0
        n_exit_early = 0
        sell_val = 0.0
        buy_val = 0.0
        x_exec = 0.0
        x_dep = 0.0
        early_val = 0.0
        renew_exec = 0
        lclosed = 0
        ldue = 0
        tl0 = S_i[SI_NTL]
        Vp = V_pre if V_pre > 1e-12 else 1e-12
        used_reg = 0.0
        if need_tag > 1e-12 and (fund == FD_NATIVE or fund == FD_NEXT):
            if lag == 1:
                kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, need_tag, seg_due, seg_amt)
                if kk < 0:
                    if err9 == 12:                     # 舍入级缺口：只消耗实际可用标签，不报错
                        av0 = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
                        kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(need_tag, av0), seg_due, seg_amt)
                        used_reg = min(need_tag, av0)
                    else:
                        S_i[SI_ERR] = 5
                else:
                    used_reg = need_tag
        for k in range(nt):
            s = tlist[k]
            P = pv[d, s]
            if not (P > 0.0):
                continue
            bq, sq = exec_qty(s, d, zr, zx, zd, P, S_req[s], B_r[s], B_x[s], B_d[s], isopen, sellable, buyable, ideal)
            full = sq >= S_req[s] * (1.0 - 1e-12)
            left = sq
            for pass_ in range(2):
                want = LQ_DUE if pass_ == 0 else LQ_EARLY
                while left > 1e-15 or full:
                    best = -1
                    j = head[s]
                    while j >= 0:
                        if L_i[j, 7] == 1 and L_i[j, 3] == want and L_f[j, 0] > 0.0:
                            if best < 0 or L_i[j, 2] < L_i[best, 2] or (L_i[j, 2] == L_i[best, 2] and L_id[j] < L_id[best]):
                                best = j
                        j = nxt[j]
                    if best < 0:
                        break
                    if full or left >= L_f[best, 0] * (1.0 - 1e-9):
                        v = L_f[best, 0]
                    else:
                        v = left
                    L_f[best, 0] -= v
                    if L_f[best, 0] < 0.0:
                        L_f[best, 0] = 0.0
                    left -= v
                    if left < 0.0:
                        left = 0.0
                    val = v * P
                    is_early = want == LQ_EARLY and d < L_i[best, 2]
                    rr = L_i[best, 6]
                    rkind = KD_TRIG
                    if rr >= 0:
                        rkind = IN_i[rr, IN_KIND]
                    if tlog:
                        okind = OK_DUE
                        if want == LQ_EARLY:
                            okind = OK_RENEW if rkind == KD_RENEW else OK_EXIT
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[best], rr, okind, 1, v, P, L_i[best, 2])
                    if is_early:
                        early_val += val
                        if n_leg < leg_due.shape[0]:
                            leg_due[n_leg] = L_i[best, 2]
                            leg_val[n_leg] = val
                            n_leg += 1
                        else:
                            S_i[SI_ERR] = 10
                        if L_i[best, 2] > last_exit_due[s]:
                            last_exit_due[s] = L_i[best, 2]
                    if L_f[best, 0] <= 1e-15:
                        L_f[best, 0] = 0.0
                        L_i[best, 7] = 0
                        hdl = d - L_i[best, 1]
                        LOTH[min(max(hdl, 0), LOTH.shape[0] - 1)] += 1
                        lclosed += 1
                        S_i[SI_LCLOSED] += 1
                        if d >= L_i[best, 2]:
                            ldue += 1
                            S_i[SI_LDUE] += 1
                        if rr >= 0:
                            IN_i[rr, IN_EXEC] = d
                            if is_early:
                                IN_i[rr, IN_STATUS] = 1
                                n_exit_early += 1
                                if rkind == KD_RENEW:
                                    renew_exec += 1
                                hd = d - L_i[best, 1]
                                HOLDH[min(max(hd, 0), HOLDH.shape[0] - 1)] += 1
                            else:
                                IN_i[rr, IN_STATUS] = 2
            sq = sq - left
            q[s] -= sq
            sell_val += sq * P
            if bq > 0.0:
                tot_b = zr * B_r[s] + zx * B_x[s] + zd * B_d[s]
                fr = (zr * B_r[s]) / tot_b if tot_b > 0 else 0.0
                fd = (zd * B_d[s]) / tot_b if tot_b > 0 else 0.0
                qr = bq * fr
                qd = bq * fd
                qx = bq - qr - qd
                if qr > 1e-15:
                    nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 0, qr)
                    if tlog and nj >= 0:
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_REGULAR, 0, qr, P, d + H)
                if qx > 1e-15:
                    x_exec += qx * P
                    if remain and fund == FD_NATIVE:
                        kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, qx * P, seg_due, seg_amt)
                        if kk < 0:
                            S_i[SI_ERR] = 4
                            nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 1, qx)
                            if tlog and nj >= 0:
                                tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qx, P, d + H)
                        else:
                            for k3 in range(kk):
                                due3 = seg_due[k3] if seg_due[k3] >= d + 1 else d + 1
                                nj = new_lot(L_i, L_f, L_id, S_i, s, d, due3, P, sig20[d, s], 2, seg_amt[k3] / P)
                                if tlog and nj >= 0:
                                    tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, seg_amt[k3] / P, P, due3)
                    else:
                        nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 1, qx)
                        if tlog and nj >= 0:
                            tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qx, P, d + H)
                if qd > 1e-15:
                    x_dep += qd * P
                    nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 3, qd)
                    if tlog and nj >= 0:
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qd, P, d + H)
                if last_exit_due[s] > d:
                    S_i[SI_REENTRY] += 1
                    DY[d, 38] += 1
                q[s] += bq
                buy_val += bq * P
            if min(sq, bq) > 1e-15:
                n_int += 1
            dn = abs(bq - sq) * P
            net_abs += dn
            if dn > 0.0:
                sg = sig20[d, s]
                av = adv20[d, s]
                if np.isfinite(sg) and np.isfinite(av) and av > 0.0:
                    imp += (dn / Vp) ** 1.5 * sg / np.sqrt(av)
                    if Vprev0 > 0.0:
                        s05 += (dn / Vprev0) * sg * sp0 * (dn / (V0 * av * p0)) ** 0.5
                        s07 += (dn / Vprev0) * sg * sp0 * (dn / (V0 * av * p0)) ** 0.7
                    if fb_on:
                        fimp += fb_cost(dn, sg, av, fbA, fbK, fbD, p0, V0)
                else:
                    qmiss += dn
        F = c * net_abs + fimp
        den = sell_val + buy_val
        fsh = F / den if den > 0 else 0.0
        if tlog:
            tnot = 0.0
            for r in range(tl0, S_i[SI_NTL]):
                tnot += TL_f[r, 1]
            if tnot > 0.0:
                for r in range(tl0, S_i[SI_NTL]):
                    TL_f[r, 3] = F * TL_f[r, 1] / tnot
        # 早退标签 / 锁定（逐腿：金额 = 毛款 − 分摊费，due = 被关闭批次原 due）；HALF：η 进标签（lag1）、1 − η 锁到原 due
        if exit_on and n_leg > 0:
            for k in range(n_leg):
                amt = leg_val[k] * (1.0 - fsh)
                if fund == FD_NATIVE or fund == FD_NEXT:
                    if rmode == RY_HALF:
                        a1 = amt * eta
                        a2 = amt - a1
                        tk_add(TK_f, TK_i, S_i, a1, d + (0 if lag == 0 else 1), max(leg_due[k], d + (0 if lag == 0 else 1)), SI_NTK)
                        DY[d, 34] += a1
                        tk_add(LK_f, LK_i, S_i, a2, d, max(leg_due[k], d), SI_NLK)
                        DY[d, 36] += a2
                    else:
                        tk_add(TK_f, TK_i, S_i, amt, d + (0 if lag == 0 else 1), max(leg_due[k], d + (0 if lag == 0 else 1)), SI_NTK)
                        DY[d, 34] += amt
                elif fund == FD_CASH:
                    tk_add(LK_f, LK_i, S_i, amt, d, max(leg_due[k], d), SI_NLK)
                    DY[d, 36] += amt
        if need_tag > 1e-12 and (fund == FD_NATIVE or fund == FD_NEXT) and lag == 0:
            av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
            kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(need_tag, av), seg_due, seg_amt)
            used_reg = min(need_tag, av)
        used_ext = 0.0
        if x_exec > 1e-12 and not (remain and fund == FD_NATIVE) and (fund == FD_NATIVE or fund == FD_NEXT):
            av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
            if x_exec > av + 1e-7 * max(1.0, V_pre):
                S_i[SI_ERR] = 6
            kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(x_exec, av), seg_due, seg_amt)
            used_ext = min(x_exec, av)
        elif x_exec > 1e-12:
            used_ext = x_exec
        cash1 = cash0 + sell_val - buy_val - F
        S_f[SF_CASH] = cash1
        if cash1 < -1e-7 * max(1.0, V_pre):
            S_i[SI_ERR] = 7
        V_post = V_pre - F
        Vprev = S_f[SF_VPREV]
        r_net = V_post / Vprev - 1.0 if Vprev > 0 else 0.0
        x_prev = S_f[SF_XPREV]
        bch = bench[d]
        if np.isfinite(bch):
            nex = r_net - x_prev * bch
        else:
            nex = r_net if x_prev == 0.0 else np.nan
        hv = 0.0
        stale = 0.0
        xval = 0.0
        nh = 0
        nlive = 0
        for g in range(G):
            indval[g] = 0.0
        for k in range(nt):
            head[tlist[k]] = -1
        for j in range(S_i[SI_NL]):
            if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                s = L_i[j, 0]
                v = L_f[j, 0] * pv[d, s]
                hv += v
                nlive += 1
                if L_i[j, 5] > 0:
                    xval += v
                if pvage[d, s] > 0:
                    stale += v
                g = ind[d, s]
                if g >= 0:
                    indval[g] += v
                if not held_mark[s]:
                    held_mark[s] = True
                    nh += 1
        sa_sum = 0.0
        sa_n = 0
        for j in range(S_i[SI_NL]):
            if L_i[j, 7] == 1:
                s = L_i[j, 0]
                if held_mark[s]:
                    held_mark[s] = False
                    held2[s] = True
                    if first_held[s] < 0:
                        first_held[s] = d
                    sa_sum += d - first_held[s]
                    sa_n += 1
        for s in range(N):
            if held2[s]:
                held2[s] = False
            elif first_held[s] >= 0:
                first_held[s] = -1
        sam = 0.0
        if V_post > 0.0:
            for g in range(G):
                a_ = indval[g] / V_post - capsh[d, g]
                if a_ > sam:
                    sam = a_
        DY[d, 0] = V_pre
        DY[d, 1] = V_post
        DY[d, 2] = F
        DY[d, 3] = hv / V_post if V_post > 0 else 0.0
        DY[d, 4] = bch
        DY[d, 5] = nex
        DY[d, 6] = cash1 / V_post if V_post > 0 else 0.0
        DY[d, 7] = nh
        DY[d, 8] = n_exit_early
        DY[d, 9] = r_net
        DY[d, 10] = net_abs
        DY[d, 11] = imp
        DY[d, 12] = qmiss
        DY[d, 19] = x_prev
        DY[d, 20] = n_int
        DY[d, 21] = buy_val
        DY[d, 22] = sell_val
        DY[d, 25] = stale
        DY[d, 27] = early_val
        DY[d, 28] = zr
        DY[d, 29] = zx
        DY[d, 30] = used_reg
        DY[d, 31] = used_ext
        DY[d, 39] = s05
        DY[d, 40] = s07
        DY[d, 42] = x_dep
        DY[d, 44] = zd
        DY[d, 45] = r_net - bch if np.isfinite(bch) else np.nan
        DY[d, 47] = nlive
        DY[d, 48] = fimp
        DY[d, 61] = sam * 100.0
        DY[d, 62] = sa_sum
        DY[d, 63] = sa_n
        DY[d, 64] = xval / V_post if V_post > 0 else 0.0
        DY[d, 65] = renew_exec
        DY[d, 66] = lclosed
        DY[d, 67] = ldue
        DY[d, 74] = n_exit_early
        S_i[SI_INTERNAL] += n_int
        S_f[SF_VPREV] = V_post
        S_f[SF_XPREV] = hv / V_post if V_post > 0 else 0.0
        for k in range(nt):
            s = tlist[k]
            S_req[s] = 0.0
            S_early_req[s] = 0.0
            B_r[s] = 0.0
            B_x[s] = 0.0
            B_d[s] = 0.0
            touched[s] = False
        S_i[SI_NPB] = 0
        if S_i[SI_NL] > 0.70 * L_i.shape[0]:
            compact_lots(L_i, L_f, L_id, IN_i, S_i)
        # ================= 收盘（d）
        nl = S_i[SI_NL]
        NAVc = S_f[SF_CASH]
        for j in range(nl):
            if L_i[j, 7] == 1:
                NAVc += L_f[j, 0] * pc[d, L_i[j, 0]]
                if L_i[j, 1] == d:
                    L_f[j, 2] = cvr[d, L_i[j, 0]]
        DY[d, 17] = NAVc
        DY[d, 16] = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, False)
        DY[d, 26] = tk_sum(LK_f, LK_i, S_i[SI_NLK], d, False)
        S_f[SF_LOCKDAYS] += DY[d, 16] + DY[d, 26]
        if d + 1 >= T:
            continue
        n_int_today = 0
        for k in range(N):
            sec_new_int[k] = False
            sec_due_max[k] = -1
        nrisk = 0
        for j in range(nl):
            if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2]:
                nrisk += 1
                RISK[d, min(d - L_i[j, 1], NL - 1)] += 1
        DY[d, 33] = nrisk
        if exit_on or shadow:
            if smode == SM_REAL or shadow:
                for j in range(nl):
                    if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
                        continue
                    s = L_i[j, 0]
                    hit = False
                    unk = False
                    if tmode == TM_PANEL:
                        v = trig[d, s]
                        hit = v == 1
                        unk = v < 0
                    elif tmode == TM_ALLFIRST:
                        hit = True
                    if unk:
                        S_i[SI_UNKDAYS] += 1
                    if not hit:
                        continue
                    if shadow:
                        HITS[d, min(d - L_i[j, 1], NL - 1)] += 1
                        continue
                    n_int_today += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                              t1a, lvl, recon, u_ptr, u_col, KD_TRIG)
                if tmode == TM_PANEL and not shadow:
                    noact = 0
                    for j in range(nl):
                        if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                            s = L_i[j, 0]
                            if not held_mark[s]:
                                held_mark[s] = True
                                if trig[d, s] == 1 and not sec_new_int[s]:
                                    noact += 1
                    for j in range(nl):
                        if L_i[j, 7] == 1:
                            held_mark[L_i[j, 0]] = False
                    S_i[SI_NOACT] += noact
                    DY[d, 68] = noact
            elif smode >= SM_AMT2 and smode != SM_RCHK:
                n_int_today += select_v2(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
                                         tg_b, tg_isk2, tg_aisk, sec_new_int, sec_due_max, DY)
            elif smode == SM_BERN:
                n_int_today += select_bern(d, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, p_bern,
                                           sec_new_int, sec_due_max)
        # ---- RENEW5：检查点重新确认（自然名单 = 无记忆源形成名单；UNKNOWN 不发单；due 不变）
        if renew > 0 and not shadow:
            known_day = nf_ptr[d + 1] > nf_ptr[d]
            nck = 0
            ncf = 0
            nrj = 0
            nuk = 0
            rq = 0
            for j in range(nl):
                if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
                    continue
                age_e = d + 1 - L_i[j, 1]
                if age_e <= 0 or age_e % renew != 0:
                    continue
                s = L_i[j, 0]
                nck += 1
                if renewok or smode == SM_RCHK:
                    if renewok:
                        ncf += 1
                    continue
                if not known_day or not isopen[d, s]:
                    nuk += 1
                    continue
                if in_csr(nf_ptr, nf_col, d, s):
                    ncf += 1
                else:
                    nrj += 1
                    rq += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                     t1a, lvl, recon, u_ptr, u_col, KD_RENEW)
            if smode == SM_RCHK and tg_rchk[d] > 1e-12:
                rq += select_rchk(d, seed, NL, renew, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, tg_rchk[d],
                                  sec_new_int, sec_due_max, DY)
            n_int_today += rq
            S_i[SI_RCHK] += nck
            S_i[SI_RCONF2] += ncf
            S_i[SI_RREJ] += nrj
            S_i[SI_RUNK] += nuk
            DY[d, 43] = rq
            DY[d, 70] = nck
            DY[d, 71] = ncf
            DY[d, 72] = nrj
            DY[d, 73] = nuk
        DY[d, 18] = n_int_today
        nl = S_i[SI_NL]
        # ---- 次日买单
        for j in range(nl):
            if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                s = L_i[j, 0]
                if L_i[j, 3] == LQ_NONE and L_i[j, 2] > d + 1:
                    expv[s] += L_f[j, 0] * pc[d, s]
        for g in range(G):
            indsum[g] = 0.0
            newsum[g] = 0.0
        for j in range(nl):
            if L_i[j, 7] == 1:
                s = L_i[j, 0]
                if expv[s] > 0.0 and not held_mark[s]:
                    held_mark[s] = True
                    g = ind[d, s]
                    if g >= 0:
                        indsum[g] += expv[s]
        for j in range(nl):
            if L_i[j, 7] == 1:
                held_mark[L_i[j, 0]] = False
        a, b = f_ptr[d], f_ptr[d + 1]
        npb = 0
        cap_s = scap * NAVc
        for k2 in range(a, b):
            s = f_col[k2]
            budget = NAVc * f_w[k2] / H
            if not (budget > 0.0):
                continue
            room = cap_s - expv[s]
            if room <= 0.0:
                continue
            PB_i[npb, 0] = s
            PB_i[npb, 1] = 0
            PB_i[npb, 2] = -1
            PB_f[npb] = min(budget, room)
            npb += 1
        for k in range(npb):
            g = ind[d, PB_i[k, 0]]
            if g >= 0:
                newsum[g] += PB_f[k]
        for k in range(npb):
            g = ind[d, PB_i[k, 0]]
            if g >= 0:
                roomg = (capsh[d, g] + idev) * NAVc - indsum[g]
                if roomg < 0.0:
                    roomg = 0.0
                if newsum[g] > roomg and newsum[g] > 0.0:
                    PB_f[k] *= roomg / newsum[g]
        for k in range(npb):
            s = PB_i[k, 0]
            expv[s] += PB_f[k]
            g = ind[d, s]
            if g >= 0:
                indsum[g] += PB_f[k]
        DY[d, 23] = 0.0
        # 额外批次计划（可用标签 K；先扣常规的预期缺口）
        extra_plan = 0.0
        if exit_on and fund == FD_NATIVE:
            K = 0.0
            for j in range(S_i[SI_NTK]):
                if TK_i[j, 2] == 1 and TK_i[j, 0] <= d + 1 and d + 1 < TK_i[j, 1]:
                    if (not remain) or TK_i[j, 1] >= d + 2:
                        K += TK_f[j]
            if K > 1e-12:
                tag_all2 = tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, False)
                lk_all2 = tk_sum(LK_f, LK_i, S_i[SI_NLK], d + 1, False)
                ordn = S_f[SF_CASH] - tag_all2 - lk_all2
                due_proc = 0.0
                for j in range(nl):
                    if L_i[j, 7] == 1 and L_f[j, 0] > 0.0 and (L_i[j, 3] == LQ_DUE or (L_i[j, 3] == LQ_NONE and L_i[j, 2] <= d + 1)):
                        due_proc += L_f[j, 0] * pc[d, L_i[j, 0]]
                regn = 0.0
                for k in range(npb):
                    regn += PB_f[k]
                short = regn - (ordn + due_proc)
                if short > 0.0:
                    K -= short
            if K > 1e-12:
                if rmode == RY_COST0 or rmode == RY_COSTNET:
                    npb, extra_plan = plan_routed(d, K, a, b, f_col, f_w, nl, L_i, L_f, pc, expv, indsum, ind, capsh, idev, cap_s, NAVc, V0,
                                                  sig20, adv20, rA, rK, rD, p0, c, rmode, PB_i, PB_f, npb, sellv, DY)
                else:
                    for k2 in range(a, b):
                        s = f_col[k2]
                        x = K * f_w[k2]
                        if not (x > 0.0):
                            continue
                        room = cap_s - expv[s]
                        g = ind[d, s]
                        if g >= 0:
                            room = min(room, (capsh[d, g] + idev) * NAVc - indsum[g])
                        if room <= 0.0:
                            continue
                        x = min(x, room)
                        PB_i[npb, 0] = s
                        PB_i[npb, 1] = 1
                        PB_i[npb, 2] = -1
                        PB_f[npb] = x
                        expv[s] += x
                        if g >= 0:
                            indsum[g] += x
                        extra_plan += x
                        npb += 1
        # ---- 部署层（TARGET / MIRROR）：只买；K_T = min{缺口, 普通现金扣计划买入与费用预留, 余量容量}
        if dmode != DP_NONE:
            tv = tgtc if dmode == DP_TARGET else tgt_expo[d]
            DY[d, 46] = tv
            if np.isfinite(tv) and tv > 0.0 and NAVc > 0.0:
                prisk = 0.0
                due_p2 = 0.0
                early_p2 = 0.0
                for j in range(nl):
                    if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                        v = L_f[j, 0] * pc[d, L_i[j, 0]]
                        if L_i[j, 3] == LQ_NONE and L_i[j, 2] > d + 1:
                            prisk += v
                        elif L_i[j, 3] == LQ_EARLY:
                            early_p2 += v
                        else:
                            due_p2 += v
                regn2 = 0.0
                for k in range(npb):
                    prisk += PB_f[k]
                    if PB_i[k, 1] == 0:
                        regn2 += PB_f[k]
                gap = tv * NAVc - prisk
                if gap < 0.0:
                    gap = 0.0
                ordn2 = S_f[SF_CASH] - tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, False) - tk_sum(LK_f, LK_i, S_i[SI_NLK], d + 1, False)
                fee_res = c * (due_p2 + early_p2 + regn2 + extra_plan + gap)
                cash_av = ordn2 + due_p2 - regn2 - fee_res
                if cash_av < 0.0:
                    cash_av = 0.0
                Kd = min(gap, cash_av / (1.0 + c))
                if zerok:
                    Kd = 0.0
                DY[d, 41] = Kd
                if Kd > 1e-9 and b > a:
                    m = b - a
                    pp = np.zeros(m)
                    cc_ = np.zeros(m)
                    gg = np.full(m, -1, np.int64)
                    gc = np.zeros(m)
                    if cmode == CP_REL:
                        scd = 1.0 / nclean[d] + 0.01 if nclean[d] > 0 else 0.01
                    elif cmode == CP_ABS01:
                        scd = 0.01
                    else:
                        scd = scap
                    for k2 in range(a, b):
                        i = k2 - a
                        s = f_col[k2]
                        pp[i] = f_w[k2] if f_w[k2] > 0.0 else 0.0
                        r_ = scd * NAVc - expv[s]
                        cc_[i] = r_ if r_ > 0.0 else 0.0
                        g = ind[d, s]
                        gg[i] = g
                        if g >= 0:
                            rg = (capsh[d, g] + idev) * NAVc - indsum[g]
                            gc[i] = rg if rg > 0.0 else 0.0
                    xd = alloc2(pp, cc_, gg, gc, Kd)
                    used = 0.0
                    for i in range(m):
                        if xd[i] > 1e-9:
                            s = f_col[a + i]
                            PB_i[npb, 0] = s
                            PB_i[npb, 1] = 2
                            PB_i[npb, 2] = -1
                            PB_f[npb] = xd[i]
                            expv[s] += xd[i]
                            g = ind[d, s]
                            if g >= 0:
                                indsum[g] += xd[i]
                            used += xd[i]
                            npb += 1
                    DY[d, 69] = used
        S_i[SI_NPB] = npb
        DY[d, 32] = extra_plan
        sn = 0.0
        sd_ = 0.0
        su = 0.0
        for k in range(npb):
            held_mark[PB_i[k, 0]] = True
        for j in range(nl):
            if L_i[j, 7] == 1:
                held_mark[L_i[j, 0]] = True
        for s in range(N):
            if held_mark[s]:
                held_mark[s] = False
                if expv[s] > 0.0:
                    z = zsz[d, s]
                    if np.isfinite(z):
                        sn += expv[s] * z
                        sd_ += expv[s]
                    else:
                        su += expv[s]
                expv[s] = 0.0
        DY[d, 13] = sn
        DY[d, 14] = sd_
        DY[d, 15] = su
    return 0


@njit(cache=True)
def select_bern(d, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, p_bern, sec_new_int, sec_due_max):
    """BERNOULLI_LAG60：逐批概率 = owner 同 H 无退出父影子风险集前 60 日已成熟触发率（p_bern[d, 日龄层]，历史不足 NaN = 不抽）。"""
    nl = S_i[SI_NL]
    nsel = 0
    for j in range(nl):
        if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
            continue
        lay = min(d - L_i[j, 1], NL - 1)
        p = p_bern[d, lay]
        if np.isfinite(p) and p > 0.0 and hash_u(seed, d, L_id[j]) < p:
            nsel += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, KD_RAND)
    return nsel


@njit(cache=True)
def take_amount(d, j, tgt, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, sec_new_int, sec_due_max, kind):
    """对批次 j 取 min(批次市值, tgt) 的持有许可（末批可部分：拆出新批次并标意向；原批次余量保留）。返回 (取得金额, 是否整批)。"""
    s = L_i[j, 0]
    v = L_f[j, 0] * pc[d, s]
    if not (v > 0.0):
        return 0.0, False
    if v > tgt + 1e-12:
        frac = tgt / v
        nj = new_lot(L_i, L_f, L_id, S_i, s, L_i[j, 1], L_i[j, 2], L_f[j, 1], L_f[j, 3], L_i[j, 5], L_f[j, 0] * frac)
        if nj < 0:
            return 0.0, False
        L_f[nj, 2] = L_f[j, 2]
        L_f[j, 0] -= L_f[nj, 0]
        mark_early(d, nj, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[nj, 1], NL - 1), sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind)
        return tgt, False
    mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind)
    return v, True


@njit(cache=True)
def select_v2(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
              tg_b, tg_isk2, tg_aisk, sec_new_int, sec_due_max, DY):
    """V2 随机 / 水平控制（plan §8.1；只用本路径 T 收盘库存与 owner T 收盘意向目标）：
    AMT2 / LVL2：日龄桶内同金额 → 本路径全部 R_INTENT 回填（LVL2 = 当日日 CVR 位置降序，确定性）；AISK2：行业 × size × 日龄桶内同金额 → 全域回填；
    ISK2：行业 × size × 日龄桶同唯一证券数 → 行业 × 日龄 → 日龄 依次回填（证券全部可干预批次一起）。每日记 requested / within / cross / unmatched。"""
    nl = S_i[SI_NL]
    cnt = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0:
            cnt += 1
    req = 0.0
    nreq = 0
    if smode == SM_ISK2 or smode == SM_AISK2:
        for k in range(tg_isk2.shape[1] if smode == SM_ISK2 else tg_aisk.shape[1]):
            v = tg_isk2[d, k] if smode == SM_ISK2 else tg_aisk[d, k]
            if v > 0:
                req += v
                nreq += 1
    else:
        for k in range(NB):
            if tg_b[d, k] > 1e-12:
                req += tg_b[d, k]
                nreq += 1
    if req <= 1e-12:
        return 0
    DY[d, 49] += req
    DY[d, 53] += nreq
    if cnt == 0:
        DY[d, 52] += req
        DY[d, 54] += 1
        return 0
    lots = np.empty(cnt, np.int64)
    key = np.empty(cnt, np.int64)
    k = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0:
            lots[k] = j
            key[k] = (L_i[j, 0] * 8192 + L_i[j, 2]) * 67108864 + (L_id[j] % 67108864)
            k += 1
    o = np.argsort(key)
    lots = lots[o]
    nsec = 0
    for k in range(cnt):
        if k == 0 or L_i[lots[k], 0] != L_i[lots[k - 1], 0]:
            nsec += 1
    sec_l = np.empty(nsec, np.int64)
    st0 = np.empty(nsec, np.int64)
    en0 = np.empty(nsec, np.int64)
    m = -1
    for k in range(cnt):
        if k == 0 or L_i[lots[k], 0] != L_i[lots[k - 1], 0]:
            m += 1
            sec_l[m] = L_i[lots[k], 0]
            st0[m] = k
        en0[m] = k + 1
    sk = np.empty(nsec)
    for i in range(nsec):
        s = sec_l[i]
        if smode == SM_LVL2:
            v = cpct[d, s]
            sk[i] = -v if np.isfinite(v) else 2.0 + s * 1e-9
        else:
            sk[i] = hash_u(seed, d, s)
    order = np.argsort(sk, kind='mergesort')
    nsel = 0
    within = 0.0
    cross = 0.0
    if smode == SM_AMT2 or smode == SM_LVL2:
        left_all = 0.0
        for bkt in range(NB):
            tgt = tg_b[d, bkt]
            if not (tgt > 1e-12):
                continue
            for oi in range(nsec):
                if tgt <= 1e-12:
                    break
                i = order[oi]
                for li in range(st0[i], en0[i]):
                    if tgt <= 1e-12:
                        break
                    j = lots[li]
                    if L_i[j, 3] != LQ_NONE:
                        continue
                    if bucket_of(d + 1 - L_i[j, 1]) != bkt:
                        continue
                    got, whole = take_amount(d, j, tgt, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col,
                                             sec_new_int, sec_due_max, KD_RAND)
                    if got > 0.0:
                        nsel += 1
                        within += got
                        tgt -= got
            if tgt > 1e-12:
                left_all += tgt
        if left_all > 1e-12:
            for oi in range(nsec):
                if left_all <= 1e-12:
                    break
                i = order[oi]
                for li in range(st0[i], en0[i]):
                    if left_all <= 1e-12:
                        break
                    j = lots[li]
                    if L_i[j, 3] != LQ_NONE or L_i[j, 7] != 1:
                        continue
                    got, whole = take_amount(d, j, left_all, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col,
                                             sec_new_int, sec_due_max, KD_RAND)
                    if got > 0.0:
                        nsel += 1
                        cross += got
                        left_all -= got
    elif smode == SM_AISK2:
        NC = tg_aisk.shape[1] // NB
        left_all = 0.0
        for cb in range(NC * NB):
            tgt = tg_aisk[d, cb]
            if not (tgt > 1e-12):
                continue
            cell = cb // NB
            bkt = cb % NB
            for oi in range(nsec):
                if tgt <= 1e-12:
                    break
                i = order[oi]
                if iskid[d, sec_l[i]] != cell:
                    continue
                for li in range(st0[i], en0[i]):
                    if tgt <= 1e-12:
                        break
                    j = lots[li]
                    if L_i[j, 3] != LQ_NONE:
                        continue
                    if bucket_of(d + 1 - L_i[j, 1]) != bkt:
                        continue
                    got, whole = take_amount(d, j, tgt, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col,
                                             sec_new_int, sec_due_max, KD_RAND)
                    if got > 0.0:
                        nsel += 1
                        within += got
                        tgt -= got
            if tgt > 1e-12:
                left_all += tgt
        if left_all > 1e-12:
            for oi in range(nsec):
                if left_all <= 1e-12:
                    break
                i = order[oi]
                for li in range(st0[i], en0[i]):
                    if left_all <= 1e-12:
                        break
                    j = lots[li]
                    if L_i[j, 3] != LQ_NONE or L_i[j, 7] != 1:
                        continue
                    got, whole = take_amount(d, j, left_all, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col,
                                             sec_new_int, sec_due_max, KD_RAND)
                    if got > 0.0:
                        nsel += 1
                        cross += got
                        left_all -= got
    elif smode == SM_ISK2:
        NC = tg_isk2.shape[1] // NB
        need = tg_isk2[d].copy()
        domb = np.full(nsec, -1, np.int64)
        for i in range(nsec):
            bv = -1.0
            bd = 1 << 40
            for li in range(st0[i], en0[i]):
                j = lots[li]
                v = L_f[j, 0] * pc[d, L_i[j, 0]]
                if v > bv or (v == bv and L_i[j, 2] < bd):
                    bv = v
                    bd = L_i[j, 2]
                    domb[i] = bucket_of(d + 1 - L_i[j, 1])
        usedsec = np.zeros(nsec, np.bool_)
        n1 = 0.0
        for oi in range(nsec):
            i = order[oi]
            cell = iskid[d, sec_l[i]]
            if cell < 0 or cell >= NC:
                continue
            idx = cell * NB + domb[i]
            if need[idx] > 0:
                for li in range(st0[i], en0[i]):
                    j = lots[li]
                    if L_i[j, 3] == LQ_NONE and L_i[j, 7] == 1:
                        nsel += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND)
                need[idx] -= 1
                usedsec[i] = True
                n1 += 1.0
        nind = NC // 3
        need2 = np.zeros(nind * NB, np.int64)
        need3 = np.zeros(NB, np.int64)
        for idx in range(NC * NB):
            if need[idx] > 0:
                ci = (idx // NB) // 3
                if ci < nind:
                    need2[ci * NB + idx % NB] += need[idx]
                else:                                  # owner 证券层未知（行业 / size 缺）：直接回填到日龄桶层
                    need3[idx % NB] += need[idx]
        n2 = 0.0
        for oi in range(nsec):
            i = order[oi]
            if usedsec[i]:
                continue
            cell = iskid[d, sec_l[i]]
            if cell < 0 or cell >= NC:
                continue
            i2 = (cell // 3) * NB + domb[i]
            if need2[i2] > 0:
                for li in range(st0[i], en0[i]):
                    j = lots[li]
                    if L_i[j, 3] == LQ_NONE and L_i[j, 7] == 1:
                        nsel += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND)
                need2[i2] -= 1
                usedsec[i] = True
                n2 += 1.0
        for i2 in range(nind * NB):
            need3[i2 % NB] += need2[i2]
        for oi in range(nsec):
            i = order[oi]
            if usedsec[i]:
                continue
            bk = domb[i]
            if need3[bk] > 0:
                for li in range(st0[i], en0[i]):
                    j = lots[li]
                    if L_i[j, 3] == LQ_NONE and L_i[j, 7] == 1:
                        nsel += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND)
                need3[bk] -= 1
                usedsec[i] = True
                n2 += 1.0
        within = n1
        cross = n2
    unm = req - within - cross
    if unm < 0.0:
        unm = 0.0
    DY[d, 50] += within
    DY[d, 51] += cross
    DY[d, 52] += unm
    if unm > 1e-9:
        DY[d, 54] += 1
    return nsel


@njit(cache=True)
def select_rchk(d, seed, NL, renew, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, tgt, sec_new_int, sec_due_max, DY):
    """R_CHECKPOINT：只在同五日检查点批次内、按稳定哈希序取消与 owner 同金额的持有许可（末批可部分）；非检查点不随机退出。"""
    nl = S_i[SI_NL]
    cnt = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0:
            age_e = d + 1 - L_i[j, 1]
            if age_e > 0 and age_e % renew == 0:
                cnt += 1
    DY[d, 49] += tgt
    DY[d, 53] += 1
    if cnt == 0:
        DY[d, 52] += tgt
        DY[d, 54] += 1
        return 0
    cand = np.empty(cnt, np.int64)
    key = np.empty(cnt)
    k = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0:
            age_e = d + 1 - L_i[j, 1]
            if age_e > 0 and age_e % renew == 0:
                cand[k] = j
                key[k] = hash_u(seed, d, L_id[j])
                k += 1
    o = np.argsort(key, kind='mergesort')
    left = tgt
    got_all = 0.0
    nsel = 0
    for oi in range(cnt):
        if left <= 1e-12:
            break
        j = cand[o[oi]]
        got, whole = take_amount(d, j, left, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, sec_new_int, sec_due_max, KD_RCHK)
        if got > 0.0:
            nsel += 1
            got_all += got
            left -= got
    DY[d, 50] += got_all
    if left > 1e-9:
        DY[d, 52] += left
        DY[d, 54] += 1
    return nsel


@njit(cache=True)
def plan_routed(d, K, a, b, f_col, f_w, nl, L_i, L_f, pc, expv, indsum, ind, capsh, idev, cap_s, NAVc, V0,
                sig20, adv20, rA, rK, rD, p0, c, rmode, PB_i, PB_f, npb, sellv, DY):
    """RECYCLE_COST0 / COSTNET（plan §6.6(b)(c)）：先按 NATIVE 原规则得可行额外分配 x_native 与预算 B；成本未知（σ / ADV 缺）或退化（σ = 0）名字冻结原分配；
    其余在同 B 与同单股 / 行业余量下最小化 Σ C_i(x)（COST0）或 Σ [C_i(b_i + x_i) − C_i(b_i)]（COSTNET；b = 本账户当日既有净订单 / NAV）。
    同一快照另算 native / cost0 / costnet 三种分配的局部成本（D9_recycle_local）。"""
    T = sig20.shape[0]
    N = expv.shape[0]
    G = capsh.shape[1]
    m = b - a
    if m <= 0:
        return npb, 0.0
    xn = np.zeros(m)
    rs_ = np.zeros(m)
    grp = np.full(m, -1, np.int64)
    addg = np.zeros(G)
    for i in range(m):
        s = f_col[a + i]
        g = ind[d, s]
        grp[i] = g
        rs = cap_s - expv[s]
        rs_[i] = rs if rs > 0.0 else 0.0
        x = K * f_w[a + i]
        if not (x > 0.0):
            continue
        room = rs
        if g >= 0:
            room = min(room, (capsh[d, g] + idev) * NAVc - indsum[g] - addg[g])
        if room <= 0.0:
            continue
        x = min(x, room)
        xn[i] = x
        if g >= 0:
            addg[g] += x
    Bn = 0.0
    for i in range(m):
        Bn += xn[i]
    if Bn <= 1e-12:
        return npb, 0.0
    regb = np.zeros(N)
    for k in range(npb):
        if PB_i[k, 1] == 0:
            regb[PB_i[k, 0]] += PB_f[k]
    for j in range(nl):
        if L_i[j, 7] == 1 and L_f[j, 0] > 0.0 and (L_i[j, 3] != LQ_NONE or L_i[j, 2] <= d + 1):
            sellv[L_i[j, 0]] += L_f[j, 0] * pc[d, L_i[j, 0]]
    bv = np.zeros(m)
    av_ = np.zeros(m)
    known = np.zeros(m, np.bool_)
    degen = np.zeros(m, np.bool_)
    Ar = rA * NAVc / V0
    unk_v = 0.0
    deg_v = 0.0
    for i in range(m):
        s = f_col[a + i]
        bv[i] = (regb[s] - sellv[s]) / NAVc
        if d + 1 < T:
            sg = sig20[d + 1, s]
            ad = adv20[d + 1, s]
        else:
            sg = np.nan
            ad = np.nan
        if np.isfinite(sg) and np.isfinite(ad) and ad > 0.0 and sg >= 0.0:
            if sg > 0.0:
                av_[i] = rK * sg * np.sqrt(p0) / ((ad * p0 / Ar) ** rD)
                known[i] = True
            else:
                degen[i] = True
                deg_v += xn[i]
        else:
            unk_v += xn[i]
    for j in range(nl):
        if L_i[j, 7] == 1:
            sellv[L_i[j, 0]] = 0.0
    nk = 0
    for i in range(m):
        if known[i]:
            nk += 1
    xf = xn.copy()
    if nk > 0:
        kid = np.empty(nk, np.int64)
        k = 0
        for i in range(m):
            if known[i]:
                kid[k] = i
                k += 1
        bk = np.zeros(nk)
        b0 = np.zeros(nk)
        ak = np.zeros(nk)
        uk = np.zeros(nk)
        gk = np.full(nk, -1, np.int64)
        gck = np.zeros(nk)
        Bk = 0.0
        frozen_g = np.zeros(G)
        for i in range(m):
            if not known[i] and grp[i] >= 0:
                frozen_g[grp[i]] += xn[i]
        for k in range(nk):
            i = kid[k]
            bk[k] = bv[i]
            ak[k] = av_[i]
            uk[k] = rs_[i] / NAVc
            g = grp[i]
            gk[k] = g
            if g >= 0:
                rgc = ((capsh[d, g] + idev) * NAVc - indsum[g] - frozen_g[g]) / NAVc
                gck[k] = rgc if rgc > 0.0 else 0.0
            Bk += xn[i] / NAVc
        x0 = route_solve(b0, ak, uk, gk, gck, Bk, c, rD)
        x1 = route_solve(bk, ak, uk, gk, gck, Bk, c, rD)
        s0 = 0.0
        s1 = 0.0
        for k in range(nk):
            s0 += x0[k]
            s1 += x1[k]
        ok0 = abs(s0 - Bk) <= 1e-9 * max(1.0, Bk) + 1e-12
        ok1 = abs(s1 - Bk) <= 1e-9 * max(1.0, Bk) + 1e-12
        cn = 0.0
        c0 = 0.0
        c1 = 0.0
        for k in range(nk):
            i = kid[k]
            base = bk[k]
            cb = res_cost(base, ak[k], c, rD)
            cn += res_cost(base + xn[i] / NAVc, ak[k], c, rD) - cb
            c0 += res_cost(base + x0[k], ak[k], c, rD) - cb
            c1 += res_cost(base + x1[k], ak[k], c, rD) - cb
        DY[d, 55] += Bn
        DY[d, 56] += cn * NAVc
        DY[d, 57] += c0 * NAVc
        DY[d, 58] += c1 * NAVc
        if rmode == RY_COST0 and ok0:
            for k in range(nk):
                xf[kid[k]] = x0[k] * NAVc
        elif rmode == RY_COSTNET and ok1:
            for k in range(nk):
                xf[kid[k]] = x1[k] * NAVc
    else:
        DY[d, 55] += Bn
    DY[d, 59] += unk_v
    DY[d, 60] += deg_v
    extra_plan = 0.0
    for i in range(m):
        x = xf[i]
        if x > 1e-12:
            s = f_col[a + i]
            PB_i[npb, 0] = s
            PB_i[npb, 1] = 1
            PB_i[npb, 2] = -1
            PB_f[npb] = x
            expv[s] += x
            g = ind[d, s]
            if g >= 0:
                indsum[g] += x
            extra_plan += x
            npb += 1
    return npb, extra_plan
