# -*- coding: utf-8 -*-
"""E6o 账户引擎（plan §5–§6、§8；brief §3–§4）。新代码（研究扩展），源引擎只读。numba 编译；单账户单路径一次调用；
状态全在 Python 端预分配的数组里，可从任意日 checkpoint 续跑（plan §14.2；续跑逐日一致由 S0-11 核）。

会计（POST_VWAP_EQUITY_V11，plan §5.4）：执行日 e 的 V⁻_e = 现金 + Σ 持仓 × 后复权 VWAP_e（停牌沿最近价、标陈旧）；交易后 V⁺_e = V⁻_e − F_e；
  R_net(e) = V⁺_e / V⁺_{e−1} − 1；净超额 = R_net(e) − x_{e−1} × bench(e)（x = 上一执行点交易后持仓 / V⁺）。
  费用 F = 4e−4 × Σ_证券 |净市场订单名义|（同证券同日买卖先内部转移再净额；源 8bp × ½Σ|Δact| 同单位，不再乘 2）。
批次：投资批次（入场执行日 e0、原到期 due = e0 + H、入场后复权 VWAP 成本、入场收盘日 CVR、入场前 20 日 σ）与证券库存分开；早退只提前不延长；
  到期未卖出 = 正常退出积压（不贴早退标签）；早退意向未在 due 前成交 → 迟到（失去早退标签，库存与请求保留）。
时序（plan §5.3）：T 收盘 → 触发（只看 ≤ T）→ 意向 e = T + 1；常规新批次预算 = NAV_close_T × w_source(T, i) / H（不归一）；
  新买受 单股 1% NAV_T、行业 ≤ clean 份额 + 3pp 的“交易后预期敞口”约束（先常规后额外，行业同比例削顶；幸存旧仓超标不强卖、不加仓）。
资金（plan §6.1–§6.2）：标签只记本金。ENGINE_NATIVE：早退款 − 分摊费 = 标签（lag1：下一执行日起可用；lag0：当日可用），到原 due 只重分类；
  常规买入先用普通现金（含普通卖款，费用全部由普通现金付），缺口才按 due 最早、ID 序消耗可用标签；剩余可用标签 K × w_source 成额外批次
  （RESET_H：新 H；ORIGINAL_DUE：持至所消耗标签的 due，按标签段拆批次）。CASH：早退净款锁到原 due，锁定期不付任何买入。
  NEXT_RANK：同一 K 按 T 冻结的源下一名逐名给款（1% / 行业余量），买不到留现金。
重入（plan §6.3）：ALLOW；BLOCK：首次早退意向时以本次被干预批次原 due 最大值为 until，下一执行日起禁新增买入，不滚动、不被坏状态延长；
  RECONFIRM：窗口内对应水平坏状态已知解除 ∧ 自然门 U 当日接纳 → 一次性解除（记 cleared），之后新的早退意向开新 episode。
可成交（plan §7.1）：FEASIBLE_DAILY：开盘才交易；内部转移先做；净卖需可卖（非全天一字跌停）、净买需可买（非全天一字涨停）；卖单续挂、买单作废。
  IDEALIZED_SOURCE_FILL：全部按意向日 VWAP 成交（停牌按最近价，源假设）。
随机（plan §8）：AMOUNT（同意向货币金额 × 日龄层；唯一证券候选（主本金批次定层）、稳定哈希序、证券内按 due / ID 配批、末批可部分）/ COUNT_IID /
  COUNT_ISK（行业 × size 三档 × 日龄；不足依次并到 行业 × 日龄、日龄）/ LEVEL_WORST（同金额、当日日 CVR 位置降序）/ BERNOULLI（逐批概率 = 父影子风险集前 60 日触发率）/
  RE_ELIG（RECONFIRM 附属：坏状态 × 自然门 四层同金额）；ENTRY_RANDOM：同取消新买金额、稳定哈希序随机取消。"""
import numpy as np
from numba import njit

IP_H, IP_TRIG, IP_SEL, IP_FUND, IP_LAG, IP_MAT, IP_RE, IP_GUARD, IP_EXIT, IP_IDEAL, IP_RECON, IP_SEED, IP_SHADOW, IP_NLAYER, IP_TLOG = range(15)
NIP = 16
FP_V0, FP_FEE, FP_SCAP, FP_IDEV, FP_T2, FP_T6A, FP_T6B, FP_T1C, FP_T1D = range(9)
NFP = 12
TM_NONE, TM_PANEL, TM_T1C, TM_T1D, TM_T2, TM_T2P, TM_T6A, TM_T6B, TM_ALLFIRST = range(9)
SM_REAL, SM_AMOUNT, SM_COUNT, SM_ISK, SM_LEVEL, SM_BERN, SM_REELIG = range(7)
FD_NATIVE, FD_CASH, FD_NEXT, FD_NONE = range(4)
RE_ALLOW, RE_BLOCK, RE_RECONFIRM = range(3)
GD_OFF, GD_T1A, GD_LVL, GD_RANDOM = range(4)
RC_NONE, RC_T1A, RC_LVL = range(3)
DY_COLS = ('nav_pre', 'nav_post', 'fee', 'exposure', 'bench', 'net_excess', 'cash_share', 'n_hold', 'n_exits', 'r_net',
           'traded', 'impact_br', 'qmiss', 'sz_num', 'sz_den', 'sz_unk', 'tag_amt', 'nav_close', 'n_intents', 'x_prev',
           'n_internal', 'buy_val', 'sell_val', 'cancel_val', 'unmatched_val', 'stale_val', 'lock_amt', 'early_val',
           'zr', 'zx', 'tag_use_reg', 'tag_use_ext', 'extra_plan', 'n_risk', 'tag_new', 'tag_matured', 'lock_new', 'lock_matured', 'n_reentry')
NDY = len(DY_COLS)
DYI = {k: i for i, k in enumerate(DY_COLS)}
SF_CASH, SF_VPREV, SF_XPREV, SF_LOCKDAYS = range(4)
NSF = 8
SI_NL, SI_NEXTID, SI_NTK, SI_NLK, SI_NPB, SI_NIN, SI_NTKID, SI_ERR, SI_INTERNAL, SI_REBLK, SI_RECONF, SI_REENTRY, SI_UNKDAYS, SI_NTL = range(14)
NSI = 16
IN_DAY, IN_SEC, IN_LAYER, IN_EXEC, IN_STATUS, IN_ISK, IN_RE, IN_LOT = range(8)
NIN_I = 8
LQ_NONE, LQ_EARLY, LQ_DUE = 0, 1, 2
# L_i 列：0 sec, 1 e0, 2 due, 3 req, 4 reqday, 5 extra, 6 intent row, 7 alive
# L_f 列：0 qty, 1 entry px, 2 entry close cvr, 3 sigma pre-entry


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
    """标签 / 锁定：全生命周期 ID 只增不减（到期删除后同 ID 不可再生，plan §6.1）。"""
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
def exec_qty(s, d, zr, zx, P, Sreq, Br, Bx, isopen, sellable, buyable, ideal):
    """单证券当日成交量（买 / 卖股数）：内部转移先做，净额看方向可行性。"""
    bq = (zr * Br + zx * Bx) / P
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
def solve_eval(d, zr, zx, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c):
    """返回 (S_tot, S_early, R_buy, X_buy, F)：给定缩放的当日总量。早退卖款按证券内早退请求占比分摊（DUE 先卖）。"""
    S_tot = 0.0
    S_early = 0.0
    R_buy = 0.0
    X_buy = 0.0
    net_abs = 0.0
    for k in range(nt):
        s = tlist[k]
        P = pv[d, s]
        if not (P > 0.0):
            continue
        bq, sq = exec_qty(s, d, zr, zx, P, S_req[s], B_r[s], B_x[s], isopen, sellable, buyable, ideal)
        S_tot += sq * P
        due_part = S_req[s] - S_early_req[s]
        S_early += max(0.0, sq - due_part) * P
        tot = zr * B_r[s] + zx * B_x[s]
        if tot > 0.0:
            fr = zr * B_r[s] / tot
            R_buy += bq * P * fr
            X_buy += bq * P * (1.0 - fr)
        net_abs += abs(bq - sq) * P
    return S_tot, S_early, R_buy, X_buy, c * net_abs


@njit(cache=True)
def feasible(S_tot, S_early, R_buy, X_buy, F, ordinary0, tk_usable, fund, lag, fsh_early):
    """普通现金付常规买入与全部费用；缺口与额外买入只能用可用标签（lag0 另含当日早退新标签）。"""
    E_new = S_early - fsh_early
    S_norm = S_tot - S_early
    need_tag = R_buy + F - fsh_early - S_norm - ordinary0
    if need_tag < 0.0:
        need_tag = 0.0
    if fund == FD_CASH or fund == FD_NONE:
        return need_tag <= 1e-9 and X_buy <= 1e-12, need_tag
    usable = tk_usable + (E_new if lag == 0 else 0.0)
    return need_tag + X_buy <= usable + 1e-9, need_tag


@njit(cache=True)
def step(d0, d1, ip, fp,
         pv, pc, pcobs, cvr, cpct, trig, t1a, lvl, sellable, buyable, isopen, sig20, adv20, zsz, ind, capsh, bench, pvage, iskid,
         f_ptr, f_col, f_w, u_ptr, u_col, n_ptr, n_col,
         tg_amt, tg_cnt, tg_isk, tg_re, p_bern, tg_cancel,
         L_i, L_f, L_id, q, ep_until, ep_clear, last_exit_due,
         TK_f, TK_i, LK_f, LK_i, PB_i, PB_f, S_f, S_i, IN_i, IN_f, DY, HOLDH, RISK, TL_i, TL_f):
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
    c = fp[FP_FEE]
    scap = fp[FP_SCAP]
    idev = fp[FP_IDEV]
    G = capsh.shape[1]
    S_req = np.zeros(N)
    S_early_req = np.zeros(N)
    B_r = np.zeros(N)
    B_x = np.zeros(N)
    touched = np.zeros(N, np.bool_)
    tlist = np.empty(N, np.int64)
    head = np.full(N, -1, np.int64)
    expv = np.zeros(N)
    rankv = np.full(N, -1.0)
    held_mark = np.zeros(N, np.bool_)
    seg_due = np.zeros(256, np.int64)
    seg_amt = np.zeros(256)
    indsum = np.zeros(G)
    newsum = np.zeros(G)
    sec_new_int = np.zeros(N, np.bool_)
    sec_due_max = np.full(N, -1, np.int64)
    leg_due = np.zeros(4096, np.int64)
    leg_val = np.zeros(4096)
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
            else:
                B_x[s] += PB_f[k]
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
        # 现金约束：先缩额外（zx），再缩常规（zr）
        tk_av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
        tag_all = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, False)
        lk_all = tk_sum(LK_f, LK_i, S_i[SI_NLK], d, False)
        ordinary0 = cash0 - tag_all - lk_all
        zr = 1.0
        zx = 1.0
        S_tot, S_e, R_b, X_b, F = solve_eval(d, zr, zx, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c)
        den = S_tot + R_b + X_b
        ok, need_tag = feasible(S_tot, S_e, R_b, X_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
        if not ok:
            lo, hi = 0.0, 1.0
            zx = 0.0
            S_tot, S_e, R_b, X_b, F = solve_eval(d, 1.0, 0.0, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c)
            den = S_tot + R_b + X_b
            ok0, need0 = feasible(S_tot, S_e, R_b, X_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
            if ok0:
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, F = solve_eval(d, 1.0, mid, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c)
                    den = S_tot + R_b + X_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr, zx = 1.0, lo
            else:
                zx = 0.0
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, F = solve_eval(d, mid, 0.0, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c)
                    den = S_tot + R_b + X_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr = lo
            S_tot, S_e, R_b, X_b, F = solve_eval(d, zr, zx, nt, tlist, pv, S_req, B_r, B_x, S_early_req, isopen, sellable, buyable, ideal, c)
            den = S_tot + R_b + X_b
            ok, need_tag = feasible(S_tot, S_e, R_b, X_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0)
            if not ok:
                S_i[SI_ERR] = 9                        # 连强制卖出与费用都付不起（不注资，标记）
        fsh = F / den if den > 0 else 0.0
        # 新早退标签（lag0 当日可用 → 先建后耗）；常规缺口先耗标签，再额外
        n_leg = 0
        # 执行：逐证券
        net_abs = 0.0
        imp = 0.0
        qmiss = 0.0
        n_int = 0
        n_exit_early = 0
        sell_val = 0.0
        buy_val = 0.0
        x_exec = 0.0
        early_val = 0.0
        Vp = V_pre if V_pre > 1e-12 else 1e-12
        # 先消耗常规缺口（普通优先）
        used_reg = 0.0
        if need_tag > 1e-12 and (fund == FD_NATIVE or fund == FD_NEXT):
            if lag == 1:
                kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, need_tag, seg_due, seg_amt)
                if kk < 0:
                    S_i[SI_ERR] = 5
                else:
                    used_reg = need_tag
        for k in range(nt):
            s = tlist[k]
            P = pv[d, s]
            if not (P > 0.0):
                continue
            bq, sq = exec_qty(s, d, zr, zx, P, S_req[s], B_r[s], B_x[s], isopen, sellable, buyable, ideal)
            # 卖：DUE 先、EARLY 后；同类 due 最早、ID 序。整笔可执行 → 请求批次整批卖出（不做逐批浮点相减，免残量）；
            # 部分（只内部转移）→ 按量分摊，余量 ≤ 批量 × 1e−9 视为卖完
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
                        r = L_i[best, 6]
                        if r >= 0:
                            IN_i[r, IN_EXEC] = d
                            if is_early:
                                IN_i[r, IN_STATUS] = 1
                                n_exit_early += 1
                                hd = d - L_i[best, 1]
                                HOLDH[min(max(hd, 0), HOLDH.shape[0] - 1)] += 1
                            else:
                                IN_i[r, IN_STATUS] = 2
            sq = sq - left
            q[s] -= sq
            sell_val += sq * P
            if bq > 0.0:
                tot_b = zr * B_r[s] + zx * B_x[s]
                fr = (zr * B_r[s]) / tot_b if tot_b > 0 else 0.0
                qr = bq * fr
                qx = bq - qr
                if qr > 1e-15:
                    new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 0, qr)
                if qx > 1e-15:
                    x_exec += qx * P
                    if remain and fund == FD_NATIVE:
                        kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, qx * P, seg_due, seg_amt)
                        if kk < 0:
                            S_i[SI_ERR] = 4
                            new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 1, qx)
                        else:
                            for k3 in range(kk):
                                due3 = seg_due[k3] if seg_due[k3] >= d + 1 else d + 1
                                new_lot(L_i, L_f, L_id, S_i, s, d, due3, P, sig20[d, s], 2, seg_amt[k3] / P)
                    else:
                        new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 1, qx)
                if last_exit_due[s] > d:
                    S_i[SI_REENTRY] += 1
                    DY[d, 38] += 1
                q[s] += bq
                buy_val += bq * P
            if min(sq, bq) > 1e-15:
                n_int += 1
            if tlog and (sq > 0.0 or bq > 0.0):
                r = S_i[SI_NTL]
                if r < TL_i.shape[0]:
                    TL_i[r, 0] = d
                    TL_i[r, 1] = s
                    TL_f[r, 0] = sq
                    TL_f[r, 1] = bq
                    TL_f[r, 2] = P
                    TL_f[r, 3] = early_val
                    S_i[SI_NTL] = r + 1
                else:
                    S_i[SI_ERR] = 11
            dn = abs(bq - sq) * P
            net_abs += dn
            if dn > 0.0:
                sg = sig20[d, s]
                av = adv20[d, s]
                if np.isfinite(sg) and np.isfinite(av) and av > 0.0:
                    imp += (dn / Vp) ** 1.5 * sg / np.sqrt(av)
                else:
                    qmiss += dn
        F = c * net_abs
        den = sell_val + buy_val
        fsh = F / den if den > 0 else 0.0
        # 早退标签 / 锁定（逐腿：金额 = 毛款 − 分摊费，due = 被关闭批次原 due）
        if exit_on and n_leg > 0:
            for k in range(n_leg):
                amt = leg_val[k] * (1.0 - fsh)
                if fund == FD_NATIVE or fund == FD_NEXT:
                    tk_add(TK_f, TK_i, S_i, amt, d + (0 if lag == 0 else 1), max(leg_due[k], d + (0 if lag == 0 else 1)), SI_NTK)
                    DY[d, 34] += amt
                elif fund == FD_CASH:
                    tk_add(LK_f, LK_i, S_i, amt, d, max(leg_due[k], d), SI_NLK)
                    DY[d, 36] += amt
        # lag0：常规缺口在新标签建立后再耗
        if need_tag > 1e-12 and (fund == FD_NATIVE or fund == FD_NEXT) and lag == 0:
            av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True)
            kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(need_tag, av), seg_due, seg_amt)
            used_reg = min(need_tag, av)
        # 额外（RESET_H 合计消耗；ORIGINAL_DUE 已逐段消耗）
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
        nh = 0
        for k in range(nt):
            head[tlist[k]] = -1
        for j in range(S_i[SI_NL]):
            if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                s = L_i[j, 0]
                v = L_f[j, 0] * pv[d, s]
                hv += v
                if pvage[d, s] > 0:
                    stale += v
                if not held_mark[s]:
                    held_mark[s] = True
                    nh += 1
        for j in range(S_i[SI_NL]):
            if L_i[j, 7] == 1:
                held_mark[L_i[j, 0]] = False
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
        S_i[SI_INTERNAL] += n_int
        S_f[SF_VPREV] = V_post
        S_f[SF_XPREV] = hv / V_post if V_post > 0 else 0.0
        for k in range(nt):
            s = tlist[k]
            S_req[s] = 0.0
            S_early_req[s] = 0.0
            B_r[s] = 0.0
            B_x[s] = 0.0
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
            if tmode == TM_T1C or tmode == TM_T1D:
                cnt = 0
                for j in range(nl):
                    if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                        s = L_i[j, 0]
                        if not held_mark[s]:
                            held_mark[s] = True
                            if np.isfinite(cvr[d, s]) and isopen[d, s]:
                                cnt += 1
                vals = np.empty(cnt)
                secs = np.empty(cnt, np.int64)
                kk = 0
                for j in range(nl):
                    if L_i[j, 7] == 1:
                        s = L_i[j, 0]
                        if held_mark[s]:
                            held_mark[s] = False
                            if np.isfinite(cvr[d, s]) and isopen[d, s]:
                                vals[kk] = cvr[d, s]
                                secs[kk] = s
                                kk += 1
                if cnt > 0:
                    rk = mid_rank(vals)
                    for k in range(cnt):
                        rankv[secs[k]] = rk[k]
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
                    elif tmode == TM_T1C or tmode == TM_T1D:
                        if rankv[s] < 0:
                            unk = True
                        else:
                            hit = rankv[s] >= (fp[FP_T1C] if tmode == TM_T1C else fp[FP_T1D])
                    elif tmode == TM_T2 or tmode == TM_T2P:
                        a0 = L_f[j, 2]
                        b0 = cvr[d, s]
                        if np.isfinite(a0) and np.isfinite(b0):
                            hit = (b0 - a0) >= fp[FP_T2]
                            if tmode == TM_T2P and hit:
                                if t1a[d, s] < 0:
                                    unk = True
                                    hit = False
                                else:
                                    hit = t1a[d, s] == 0
                        else:
                            unk = True
                    elif tmode == TM_T6A or tmode == TM_T6B:
                        pobs = pcobs[d, s]
                        if np.isfinite(pobs) and L_f[j, 1] > 0.0:
                            loss = pobs / L_f[j, 1] - 1.0
                            if tmode == TM_T6A:
                                hit = loss <= -fp[FP_T6A]
                            else:
                                sg = L_f[j, 3]
                                if np.isfinite(sg) and sg > 0.0:
                                    hit = loss <= -fp[FP_T6B] * sg
                                else:
                                    unk = True
                        else:
                            unk = True
                    elif tmode == TM_ALLFIRST:
                        hit = True
                    if unk:
                        S_i[SI_UNKDAYS] += 1
                    if not hit:
                        continue
                    if shadow:
                        r = S_i[SI_NIN]
                        if r < IN_i.shape[0]:
                            IN_i[r, IN_DAY] = d
                            IN_i[r, IN_SEC] = s
                            IN_i[r, IN_LAYER] = min(d - L_i[j, 1], NL - 1)
                            IN_i[r, IN_STATUS] = 9
                            IN_i[r, IN_LOT] = -1
                            IN_f[r, 0] = L_f[j, 0] * pc[d, s]
                            S_i[SI_NIN] = r + 1
                        continue
                    n_int_today += mark_early(d, j, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                              t1a, lvl, recon, u_ptr, u_col)
            elif exit_on:
                n_int_today += select_random(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon,
                                             u_ptr, u_col, tg_amt, tg_cnt, tg_isk, tg_re, p_bern, sec_new_int, sec_due_max, DY)
            if tmode == TM_T1C or tmode == TM_T1D:
                for j in range(nl):
                    if L_i[j, 7] == 1:
                        rankv[L_i[j, 0]] = -1.0
        DY[d, 18] = n_int_today
        nl = S_i[SI_NL]
        if remode != RE_ALLOW:
            for j in range(nl):
                s = L_i[j, 0]
                if L_i[j, 7] == 1 and sec_new_int[s]:
                    if not (ep_until[s] > d + 1 and ep_clear[s] == 0):
                        ep_until[s] = sec_due_max[s]
                        ep_clear[s] = 0
                    sec_new_int[s] = False
            if remode == RE_RECONFIRM:
                for s in range(N):
                    if ep_until[s] > d + 1 and ep_clear[s] == 0:
                        st = t1a[d, s] if recon == RC_T1A else lvl[d, s]
                        if st == 0 and in_csr(u_ptr, u_col, d, s):
                            ep_clear[s] = 1
                            S_i[SI_RECONF] += 1
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
        cancel_val = 0.0
        cap_s = scap * NAVc
        for k2 in range(a, b):
            s = f_col[k2]
            budget = NAVc * f_w[k2] / H
            if not (budget > 0.0):
                continue
            if remode != RE_ALLOW and ep_until[s] > d + 1 and ep_clear[s] == 0:
                S_i[SI_REBLK] += 1
                continue
            if guard == GD_T1A and t1a[d, s] == 1:
                cancel_val += budget
                continue
            if guard == GD_LVL and lvl[d, s] == 1:
                cancel_val += budget
                continue
            room = cap_s - expv[s]
            if room <= 0.0:
                continue
            PB_i[npb, 0] = s
            PB_i[npb, 1] = 0
            PB_i[npb, 2] = -1
            PB_f[npb] = min(budget, room)
            npb += 1
        if guard == GD_RANDOM and tg_cancel[d] > 0.0 and npb > 0:
            tgt = tg_cancel[d]
            keys = np.empty(npb)
            for k in range(npb):
                keys[k] = hash_u(seed, d, PB_i[k, 0])
            order = np.argsort(keys)
            for kk in range(npb):
                if tgt <= 1e-12:
                    break
                k = order[kk]
                v = min(PB_f[k], tgt)
                PB_f[k] -= v
                tgt -= v
                cancel_val += v
            if tgt > 1e-12:
                DY[d, 24] += tgt
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
        DY[d, 23] = cancel_val
        # 额外批次计划（可用标签 K；先扣常规的预期缺口）
        extra_plan = 0.0
        if exit_on and (fund == FD_NATIVE or fund == FD_NEXT):
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
                if fund == FD_NATIVE:
                    for k2 in range(a, b):
                        s = f_col[k2]
                        x = K * f_w[k2]
                        if not (x > 0.0):
                            continue
                        if remode != RE_ALLOW and ep_until[s] > d + 1 and ep_clear[s] == 0:
                            continue
                        if guard == GD_T1A and t1a[d, s] == 1:
                            continue
                        if guard == GD_LVL and lvl[d, s] == 1:
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
                else:
                    left = K
                    for k2 in range(n_ptr[d], n_ptr[d + 1]):
                        if left <= 1e-12:
                            break
                        s = n_col[k2]
                        if remode != RE_ALLOW and ep_until[s] > d + 1 and ep_clear[s] == 0:
                            continue
                        room = cap_s - expv[s]
                        g = ind[d, s]
                        if g >= 0:
                            room = min(room, (capsh[d, g] + idev) * NAVc - indsum[g])
                        if room <= 0.0:
                            continue
                        x = min(left, room)
                        PB_i[npb, 0] = s
                        PB_i[npb, 1] = 1
                        PB_i[npb, 2] = -1
                        PB_f[npb] = x
                        expv[s] += x
                        if g >= 0:
                            indsum[g] += x
                        extra_plan += x
                        left -= x
                        npb += 1
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
def mark_early(d, j, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col):
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
def exit_all_lots(d, s, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, NL, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col):
    n = 0
    for j in range(S_i[SI_NL]):
        if L_i[j, 7] == 1 and L_i[j, 0] == s and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2]:
            n += mark_early(d, j, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
    sec_new_int[s] = True
    return n


@njit(cache=True)
def select_random(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
                  tg_amt, tg_cnt, tg_isk, tg_re, p_bern, sec_new_int, sec_due_max, DY):
    """随机 / 水平控制的当日选择：只用本路径 T 收盘已知库存 / 价格与真账户 T 收盘意向目标（plan §8.1–§8.2）。"""
    nl = S_i[SI_NL]
    N = pc.shape[1]
    domv = np.zeros(N)
    doml = np.full(N, -1, np.int64)
    domdue = np.full(N, 1 << 40, np.int64)
    for j in range(nl):
        if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
            continue
        s = L_i[j, 0]
        v = L_f[j, 0] * pc[d, s]
        lay = min(d - L_i[j, 1], NL - 1)
        if v > domv[s] or (v == domv[s] and L_i[j, 2] < domdue[s]):
            domv[s] = v
            doml[s] = lay
            domdue[s] = L_i[j, 2]
    cand = np.flatnonzero(doml >= 0)
    nsel = 0
    if smode == SM_BERN:
        for j in range(nl):
            if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
                continue
            lay = min(d - L_i[j, 1], NL - 1)
            p = p_bern[d, lay]
            if np.isfinite(p) and p > 0.0 and hash_u(seed, d, L_id[j]) < p:
                nsel += mark_early(d, j, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
        return nsel
    if len(cand) == 0:
        if smode == SM_AMOUNT or smode == SM_LEVEL:
            for a in range(NL):
                DY[d, 24] += tg_amt[d, a]
        elif smode == SM_REELIG:
            for a in range(4):
                DY[d, 24] += tg_re[d, a]
        return 0
    key = np.empty(len(cand))
    for k in range(len(cand)):
        s = cand[k]
        if smode == SM_LEVEL:
            v = cpct[d, s]
            key[k] = -v if np.isfinite(v) else 2.0 + s * 1e-9
        else:
            key[k] = hash_u(seed, d, s)
    order = cand[np.argsort(key, kind='mergesort')]
    if smode == SM_AMOUNT or smode == SM_LEVEL or smode == SM_REELIG:
        nst = NL if smode != SM_REELIG else 4
        for a in range(nst):
            tgt = tg_amt[d, a] if smode != SM_REELIG else tg_re[d, a]
            if not (tgt > 1e-12):
                continue
            for s in order:
                if tgt <= 1e-12:
                    break
                if sec_new_int[s]:
                    continue
                if smode != SM_REELIG:
                    if doml[s] != a:
                        continue
                else:
                    bad = (recon == RC_T1A and t1a[d, s] == 1) or (recon == RC_LVL and lvl[d, s] == 1)
                    st = (2 if bad else 0) + (1 if in_csr(u_ptr, u_col, d, s) else 0)
                    if st != a:
                        continue
                while tgt > 1e-12:
                    best = -1
                    for j in range(S_i[SI_NL]):
                        if L_i[j, 7] == 1 and L_i[j, 0] == s and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2]:
                            if best < 0 or L_i[j, 2] < L_i[best, 2] or (L_i[j, 2] == L_i[best, 2] and L_id[j] < L_id[best]):
                                best = j
                    if best < 0:
                        break
                    v = L_f[best, 0] * pc[d, s]
                    if v > tgt + 1e-12:
                        frac = tgt / v
                        nj = new_lot(L_i, L_f, L_id, S_i, s, L_i[best, 1], L_i[best, 2], L_f[best, 1], L_f[best, 3], L_i[best, 5], L_f[best, 0] * frac)
                        if nj < 0:
                            break
                        L_f[nj, 2] = L_f[best, 2]
                        L_f[best, 0] -= L_f[nj, 0]
                        best = nj
                        v = tgt
                    nsel += mark_early(d, best, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[best, 1], NL - 1), sec_new_int, sec_due_max,
                                       t1a, lvl, recon, u_ptr, u_col)
                    tgt -= v
                sec_new_int[s] = True
            if tgt > 1e-12:
                DY[d, 24] += tgt
        return nsel
    if smode == SM_COUNT:
        for a in range(NL):
            m = tg_cnt[d, a]
            for s in order:
                if m <= 0:
                    break
                if doml[s] != a or sec_new_int[s]:
                    continue
                nsel += exit_all_lots(d, s, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, NL, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
                m -= 1
            if m > 0:
                DY[d, 24] += m
        return nsel
    if smode == SM_ISK:
        S3 = tg_isk.shape[1]
        need = tg_isk[d].copy()
        for s in order:
            st = iskid[d, s]
            if st < 0 or sec_new_int[s]:
                continue
            idx = st * NL + doml[s]
            if idx < S3 and need[idx] > 0:
                nsel += exit_all_lots(d, s, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, NL, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
                need[idx] -= 1
        nind = S3 // (3 * NL)
        need2 = np.zeros(nind * NL, np.int64)
        need3 = np.zeros(NL, np.int64)
        for idx in range(S3):
            if need[idx] > 0:
                st = idx // NL
                a = idx % NL
                need2[(st // 3) * NL + a] += need[idx]
        for s in order:
            st = iskid[d, s]
            if st < 0 or sec_new_int[s]:
                continue
            i2 = (st // 3) * NL + doml[s]
            if need2[i2] > 0:
                nsel += exit_all_lots(d, s, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, NL, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
                need2[i2] -= 1
        for i2 in range(nind * NL):
            need3[i2 % NL] += need2[i2]
        for s in order:
            if sec_new_int[s]:
                continue
            a = doml[s]
            if need3[a] > 0:
                nsel += exit_all_lots(d, s, L_i, L_f, IN_i, IN_f, S_i, pc, iskid, NL, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col)
                need3[a] -= 1
        for a in range(NL):
            if need3[a] > 0:
                DY[d, 24] += need3[a]
        return nsel
    return nsel
