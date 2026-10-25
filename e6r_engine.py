# -*- coding: utf-8 -*-
"""E6r 账户引擎 = E6q 账户引擎（e6q_engine e853439a 逐式复制；全部新开关关闭时浮点运算序列与 E6q 相同，S0-A 58 个同坐标账户逐日复现）
+ 本轮受控扩展（plan v1.1 §4–§6、§8；brief §0.1 / §1.3 / §3）：
- 入场算子（IP_OVL）：常规批次与退出款再买批次（EXTRA）先按 E6q 原式算 FLAT 票据 x⁰，再按形成层数组（ov_rho / ov_pin / ov_cell，e6r_overlay 产物）：
  GATE（GATE_STATE / DROP_T3）删票不回填不再归一；TILT（TILT_CVR_L050 / L025 / SIZE / CVR5 / GATE_TILT）q = x⁰·ρ 只乘一次，KL 投影到同 B = Σx⁰
  （单股余量 = cap 参数·NAV − 已有敞口、行业余量 = (份额 + 3pp)·NAV − 已有、NA 固定 x⁰）；CELL 另加每格预算 = Σ_cell x⁰、未知格固定；
  TILT_H 票据不变、当日新批次 due = e0 + H_by_tertile[label]（T1 30 / T2 20 / T3 10 / NA = funding_H），日资金仍按注册 funding_H。
- 入场随机（IP_ERND，plan §8.1–§8.2）：路径在自己的快照上先生成真实算子 would-be 票据，再 TICKETS（多重集首个可行双射，五日块 × 路径 × 证券键稳定优先序）/
  LABEL_PROJECT（标签多重集随机分配后同一投影器，形成层 + 账户层）/ GATE_COUNT（同快照删同数，不删 UNKNOWN）/ GATE_AMOUNT（删同名义额，末名部分）/
  JOINT（同数随机门 + 保留集 would-be 倾斜票据置换）/ TENOR（H 标签多重集随机分配）。
- GATE_REARM（IP_GR = M3 × M4 REARM，plan §5.3 / §6.5）：REARM 决定本次目标关闭量（L_f[5] = 待关闭量：首次 θ·余量、REARM 升级为余量），
  M3 按证券净单预算 p*·ADV20 每日分配（L_f[4] = 当日分配）；待处理中升级不续 deadline、不叠卖；半量完成后的 rearm 取新队列时钟、deadline ≤ 原 due。
- T1A_TIME_LEVEL_RANK（SM_TLR）：本账户当日 T1a 合法意向名义额（按日龄桶）→ 本账户 R_INTENT 按当日 cvr_pct 降序（LEVEL 坏度）选额，末批部分（select_v2 LVL2 同式）。
- 批次标签：L_i 14 cohort T0 / 15 算子标签 / 16 CVR20 标签 / 17 T0 状态；成交日志加 cohort / 标签 / 状态与形成 / 计划两层权重；PL_i / PL_f 逐证券计划标签（计划日写、成交日读）。
E6q 账户引擎原说明（保留）：
E6q 账户引擎 = E6p 账户引擎（e6p_engine 263d5cfa 逐式复制；NATIVE / CASH_REMAIN / RECYCLE_HALF 原实现保留）+ 本轮受控扩展（plan v1.1 §5–§9；brief §1.3 / §3）。
全部新扩展由新开关控制，全关时浮点运算序列与 E6p 相同（S0-G E6P_ACCOUNT_REPLICATION / S0-F 零干预与端点恒等逐日核）。
E6q 新扩展（plan §5.2–§5.6、§6.2a、§8.2–§8.3）：
- M1 REINVEST_NEW：额外批次只买 T 收盘物理库存为零的源名单名字，按 DEV 权重在新名字内重归一、单股 / 行业余量截断；未用额度不归一成杠杆。
- M2 REINVEST_LIQ：额外买 x_s ≤ max(0, B_s − b_s)，B_s = p*·ADV20_T·V0 / A_ref（A_design,T = A_ref·NAV_T / NAV_0），b_s = 次日固定净单（常规买 − 到期 / 早退卖）。
- M1 / M2 拒绝与隔离：NATIVE 同日可用额 − 本臂可用额 > 0 → 消费序对应标签 first_denied = 次日（首次拒绝起算，重复不重置）；first_denied + TTL 起隔离（额外 / 常规都不可用），
  到原 due 只解锁归属不增现金；常规缺口用标签须过同一路由（PB_i 第 2 列合格标志；min(缺口, 常规买) ≤ 合格常规买）。
- M3 EXIT_GATE_LIQ：意向固定 first_decision / deadline = min(due, first_e + 4)；每个 T 在常规计划后按证券净单 |b − s| ≤ B 分配信息卖量（队列 deadline, first_decision, lot）；
  到 deadline 强制完成（DEADLINE_OVERRIDE）；成交填充沿 E6p (due, id) 序。
- M4 EXIT_HALF：首次有效意向取剩余量 × θ 为固定目标；部分成交只续同一目标；完成后余半回持有、due 不变、不再开 episode；REARM：已知 False 后再 True 才把同一请求提到余量（UNKNOWN 不解除）。
- 影子首达（FIRSTHIT）：每批只记首次已知 True；风险要求次日执行 < due、信号已知。随机 BERNOULLI_FIRSTHIT 每批一次事件。
- RANDOM_TARGET：同票据 / 同名额在本臂合法目标集或源 cohort 内按五日块 × path × 证券固定哈希优先序求精确首个可行匹配（迭代 DFS，节点上限 → ALGORITHM_LIMIT）。
- 成本系数加 δ = 1；成交日志加 deadline 与计划名义；日序列加标签 / 隔离 / 半量 / 门控计数。
E6p 扩展（原文保留）：
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

from e6r_kl import kl_project, transport_cells, form_tilt, KL_OK

IP_H, IP_TRIG, IP_SEL, IP_FUND, IP_LAG, IP_MAT, IP_RE, IP_GUARD, IP_EXIT, IP_IDEAL, IP_RECON, IP_SEED, IP_SHADOW, IP_NLAYER, IP_TLOG = range(15)
IP_DEPLOY, IP_CAP, IP_RENEW, IP_RECYCLE, IP_FEEDBACK, IP_ZEROK, IP_RENEWOK = range(15, 22)
IP_M1, IP_M2, IP_M3, IP_HALF, IP_REARM, IP_QDAYS, IP_ROUTE, IP_RT, IP_FIRSTHIT, IP_NODES = range(24, 34)
IP_OVL, IP_ERND, IP_GR, IP_RTV = range(34, 38)      # E6r：入场算子模式、入场随机机制、GATE_REARM 组合、票据求解器版本（rt_dispatch）
NIP = 40
FP_V0, FP_FEE, FP_SCAP, FP_IDEV, FP_T2, FP_T6A, FP_T6B, FP_T1C, FP_T1D = range(9)
FP_TARGET, FP_ETA, FP_RA, FP_RK, FP_RD, FP_P0, FP_FBA, FP_FBK, FP_FBD = range(9, 18)
FP_LAMBDA, FP_RCAP = 18, 19                          # E6r：倾斜剂量 λ、形成层研究单股参数（.015）
FP_PSTAR, FP_AREF, FP_THETA = range(20, 23)
NFP = 24
OV_NONE, OV_GATE, OV_TILT, OV_TILTH, OV_CELL, OV_GATETILT = range(6)
ER_NONE, ER_TICKETS, ER_LABEL, ER_GCOUNT, ER_GAMOUNT, ER_JOINT, ER_TENOR = range(7)
NPBI = 4                                             # PB_i：0 证券、1 种类（0 常规 / 1 额外 / 2 部署）、2 路由合格、3 形成名单项 k2（E6r）
NPLI = 6                                             # PL_i：0 cohort T0、1 算子标签、2 CVR20 标签、3 T0 状态、4 分配 H、5 当日是否有计划
NPLF = 6                                             # PL_f：0 形成 b、1 形成目标 w*、2 常规计划 x、3 常规 x⁰、4 额外计划 x、5 额外 x⁰
RT_NONE, RT_WITHIN, RT_SOURCE = range(3)
RTS_NONE, RTS_FEASIBLE, RTS_NOMATCH, RTS_LIMIT, RTS_IDENTITY = range(5)
TM_NONE, TM_PANEL, TM_T1C, TM_T1D, TM_T2, TM_T2P, TM_T6A, TM_T6B, TM_ALLFIRST = range(9)
SM_REAL, SM_AMOUNT, SM_COUNT, SM_ISK, SM_LEVEL, SM_BERN, SM_REELIG, SM_AMT2, SM_ISK2, SM_LVL2, SM_AISK2, SM_RCHK = range(12)
SM_TLR = 12                                          # E6r：T1A_TIME_LEVEL_RANK
FD_NATIVE, FD_CASH, FD_NEXT, FD_NONE = range(4)
RE_ALLOW, RE_BLOCK, RE_RECONFIRM = range(3)
GD_OFF, GD_T1A, GD_LVL, GD_RANDOM = range(4)
RC_NONE, RC_T1A, RC_LVL = range(3)
DP_NONE, DP_TARGET, DP_MIRROR = range(3)
CP_SOURCE, CP_REL, CP_ABS01 = range(3)
RY_NONE, RY_HALF, RY_COST0, RY_COSTNET = range(4)
NB = 6                                   # V2 日龄桶：1 / 2 / 3–5 / 6–10 / 11–20 / 21+
KD_TRIG, KD_RENEW, KD_RAND, KD_RCHK, KD_REARM = range(5)
OK_REGULAR, OK_EXIT, OK_EXTRA, OK_RENEW, OK_DUE, OK_EXIT_HALF, OK_EXIT_REARM, OK_DEADLINE = range(8)
DY_COLS = ('nav_pre', 'nav_post', 'fee', 'exposure', 'bench', 'net_excess', 'cash_share', 'n_hold', 'n_exits', 'r_net',
           'traded', 'impact_br', 'qmiss', 'sz_num', 'sz_den', 'sz_unk', 'tag_amt', 'nav_close', 'n_intents', 'x_prev',
           'n_internal', 'buy_val', 'sell_val', 'cancel_val', 'unmatched_val', 'stale_val', 'lock_amt', 'early_val',
           'zr', 'zx', 'tag_use_reg', 'tag_use_ext', 'extra_plan', 'n_risk', 'tag_new', 'tag_matured', 'lock_new', 'lock_matured', 'n_reentry',
           'cost_s05', 'cost_s07', 'deploy_plan', 'deploy_buy', 'renew_n', 'zd', 'full_bench_ex', 'target_expo', 'n_lots', 'fb_impact',
           'v2_req', 'v2_within', 'v2_cross', 'v2_unm', 'v2_nreq', 'v2_nunm', 'rt_budget', 'rt_native', 'rt_cost0', 'rt_costnet', 'rt_unknown',
           'rt_degen', 'sector_active_max', 'sec_age_sum', 'sec_age_n', 'extra_val', 'renew_exec', 'lots_closed', 'lots_closed_due', 'noact',
           'deploy_cap_used', 'n_checkpoints', 'n_confirmed', 'n_rejected', 'n_unknown', 'early_exec_n', 'renew_qmiss',
           'cost_s10', 'tk_usable_next', 'tk_quar', 'n_tk_quar', 'deny_amt', 'deny_n', 'new_n', 'list_n', 'extra_native_plan', 'fallback_n',
           'm3_req_val', 'm3_alloc_val', 'm3_forced_val', 'm3_pending_n', 'm3_override_n', 'half_start_n', 'half_done_n', 'rearm_n',
           'rt_status', 'rt_short', 'rt_tickets', 'route_need_elig', 'new_empty', 'cash_close', 'm3_planned_buy_val', 'rt_arm_use',
           # ---- E6r（102 起）：入场算子两层预算、入场随机、GATE_REARM、T1A_TIME_LEVEL_RANK、预算桥与三层集中度
           'ov_B', 'ov_X', 'ov_gated_n', 'ov_gated_val', 'ov_active', 'ov_status', 'ov_capviol', 'ov_indviol', 'ov_na_n', 'ov_na_drift',
           'ov_cell_drift', 'ov_transfer', 'ov_xB', 'ov_xX', 'ov_cohort_n', 'ov_g', 'er_status', 'er_identity', 'er_nodes', 'er_short',
           'gr_promote', 'tlr_amt', 'paid_reg', 'paid_ext', 'n_lab_T1', 'n_lab_T3', 'h_assigned_mean', 'pa_g', 'pa_h2', 'pa_h15',
           'cap_bound_n', 'ind_bound_n', 'ah_h2', 'ah_h15', 'er_dw', 'er_dw2',
           # 入场随机每日抽样计数（常规 + 额外批次；er_status 只记常规批次）：可行非恒等 / 无解 / 触限 / 恒等 / 结构退化
           'er_c_feas', 'er_c_nom', 'er_c_lim', 'er_c_id', 'er_c_deg')
NDY = len(DY_COLS)
DYI = {k: i for i, k in enumerate(DY_COLS)}
(DY_S10, DY_TKU, DY_TKQ, DY_NTKQ, DY_DENY, DY_DENYN, DY_NEWN, DY_LISTN, DY_XNAT, DY_FALLBACK, DY_M3REQ, DY_M3ALLOC, DY_M3FORCED, DY_M3PEND,
 DY_M3OVR, DY_HALFST, DY_HALFDN, DY_REARM, DY_RTST, DY_RTSHORT, DY_RTTK, DY_RNEED, DY_NEWEMPTY, DY_CASHC, DY_M3BUY, DY_ARMUSE) = range(76, 102)
(DY_OVB, DY_OVX, DY_OVGN, DY_OVGV, DY_OVACT, DY_OVST, DY_OVCAPV, DY_OVINDV, DY_OVNAN, DY_OVNAD, DY_OVCELLD, DY_OVTRF, DY_OVXB, DY_OVXX,
 DY_OVCN, DY_OVG, DY_ERST, DY_ERID, DY_ERNODES, DY_ERSHORT, DY_GRPROM, DY_TLRAMT, DY_PAIDR, DY_PAIDX, DY_NT1, DY_NT3, DY_HMEAN,
 DY_PAG, DY_PAH2, DY_PAH15, DY_CAPBN, DY_INDBN, DY_AHH2, DY_AHH15, DY_ERDW, DY_ERDW2) = range(102, 138)
DY_ERC1 = 138                                   # er_c_feas；code k（1..5）→ DY_ERC1 + k − 1
assert NDY == 143 and DY_COLS[138] == 'er_c_feas' and DY_COLS[76] == 'cost_s10' and DY_COLS[100] == 'm3_planned_buy_val' and DY_COLS[101] == 'rt_arm_use' and DY_COLS[135] == 'ah_h15' and DY_COLS[137] == 'er_dw2'
SF_CASH, SF_VPREV, SF_XPREV, SF_LOCKDAYS = range(4)
NSF = 8
SI_NL, SI_NEXTID, SI_NTK, SI_NLK, SI_NPB, SI_NIN, SI_NTKID, SI_ERR, SI_INTERNAL, SI_REBLK, SI_RECONF, SI_REENTRY, SI_UNKDAYS, SI_NTL = range(14)
SI_LCLOSED, SI_LDUE, SI_NOACT, SI_RCHK, SI_RCONF2, SI_RREJ, SI_RUNK, SI_RNDFIX = range(14, 22)
SI_DENY, SI_QUAR, SI_OVERRIDE, SI_HALF, SI_REARMN, SI_FALLBACK, SI_RTLIM, SI_RTNOM, SI_RTID, SI_NEWEMPTY = range(24, 34)
SI_PROJF, SI_ERFEAS, SI_ERNOM, SI_ERLIM, SI_ERID = range(34, 39)       # E6r：两层投影失败、入场随机票据可行 / 无解 / 触限 / 恒等抽样
# E6r 票据求解器计数（rt_dispatch）：比对实例、v1 可行而 v2 不同解、v1 触限、其中 v2 求得首解、v2 触限、精确回溯次数、BFD 证书、2-交换证书、v1 / v2 节点和
SI_RTCMP, SI_RTMIS, SI_RTV1LIM, SI_RTV1OK, SI_RTV2LIM, SI_RTEXACT, SI_RTBFD, SI_RTSWAP, SI_RTN1, SI_RTN2 = range(40, 50)
NSI = 56
IN_DAY, IN_SEC, IN_LAYER, IN_EXEC, IN_STATUS, IN_ISK, IN_RE, IN_LOT, IN_KIND, IN_AGE, IN_DUE, IN_LID = range(12)
NIN_I = 12
LQ_NONE, LQ_EARLY, LQ_DUE = 0, 1, 2
NLI = 18                                 # E6r：+ 14 cohort T0、15 算子标签、16 CVR20 标签、17 T0 状态
NLF = 6
NTKI = 6
NTLI = 12                                # E6r：+ 8 cohort T0、9 算子标签、10 CVR20 标签、11 T0 状态
NTLF = 8                                 # E6r：+ 6 形成权重 b、7 计划账户权重（x / NAV_T）
# L_i 列：0 sec, 1 e0, 2 due, 3 req, 4 reqday, 5 extra（0 常规 / 1 额外 / 2 额外按段 / 3 部署）, 6 intent row, 7 alive,
#         8 first_decision（E6q）, 9 deadline（M3）, 10 半量状态（0 无 / 1 首次半量 / 2 REARM 升级）, 11 has_cleared, 12 已首达（影子 / BERNOULLI）, 13 强制完成标志
# L_f 列：0 qty, 1 entry px, 2 entry close cvr, 3 sigma pre-entry, 4 当日 / 待卖目标量（M3 / M4）, 5 半量快照目标
# TK_i 列：0 unlock, 1 due, 2 active, 3 id, 4 first_denied（−1 = 未被新规则拒绝）, 5 预留
# TL_i 列：0 day, 1 sec, 2 lot_id, 3 request row, 4 order_kind, 5 side（0 买 / 1 卖）, 6 lot_due, 7 deadline；TL_f 列：0 qty, 1 notional, 2 price, 3 fee, 4 计划名义（T 价）, 5 预留


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
    if L_i.shape[1] > 8:
        L_i[n, 8] = -1
        L_i[n, 9] = -1
        L_i[n, 10] = 0
        L_i[n, 11] = 0
        L_i[n, 12] = 0
        L_i[n, 13] = 0
    if L_i.shape[1] > 17:
        L_i[n, 14] = -1
        L_i[n, 15] = 0
        L_i[n, 16] = 0
        L_i[n, 17] = -1
    if L_f.shape[1] > 4:
        L_f[n, 4] = qty
        L_f[n, 5] = 0.0
    L_id[n] = S_i[SI_NEXTID]
    S_i[SI_NEXTID] += 1
    S_i[SI_NL] = n + 1
    return n


@njit(cache=True)
def lot_lab(L_i, nj, PL_i, s):
    """E6r：新批次的形成标签（计划日 PL_i 逐证券写入；只记录，不参与 E6q 运算）。"""
    if nj >= 0 and PL_i[s, 5] == 1:
        L_i[nj, 14] = PL_i[s, 0]
        L_i[nj, 15] = PL_i[s, 1]
        L_i[nj, 16] = PL_i[s, 2]
        L_i[nj, 17] = PL_i[s, 3]


@njit(cache=True)
def tl_lab(TL_i, TL_f, S_i, coh, lab, lab20, st, fw, pw):
    """E6r：成交日志最后一行补 cohort / 标签 / 状态与两层权重。"""
    r = S_i[SI_NTL] - 1
    if r >= 0 and TL_i.shape[1] > 11:
        TL_i[r, 8] = coh
        TL_i[r, 9] = lab
        TL_i[r, 10] = lab20
        TL_i[r, 11] = st
        TL_f[r, 6] = fw
        TL_f[r, 7] = pw


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
    if TK_i.shape[1] > 4:
        TK_i[n, 4] = -1
        TK_i[n, 5] = 0
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
                for cc in range(TK_i.shape[1]):
                    TK_i[k, cc] = TK_i[j, cc]
            k += 1
    S_i[nslot] = k


@njit(cache=True)
def tk_ok(TK_i, j, day, ttl):
    """标签 j 在 day 是否可用：已解锁、早于原 due、未被新规则隔离（first_denied + ttl 起隔离；ttl ≤ 0 = 不适用，与 E6p 同式）。"""
    if not (TK_i[j, 0] <= day and day < TK_i[j, 1]):
        return False
    if ttl > 0 and TK_i.shape[1] > 4 and TK_i[j, 4] >= 0 and day >= TK_i[j, 4] + ttl:
        return False
    return True


@njit(cache=True)
def tk_sum(TK_f, TK_i, n, day, usable_only, ttl):
    s = 0.0
    for j in range(n):
        if TK_i[j, 2] == 1:
            if usable_only:
                if tk_ok(TK_i, j, day, ttl):
                    s += TK_f[j]
            else:
                s += TK_f[j]
    return s


@njit(cache=True)
def tk_quar(TK_f, TK_i, n, day, ttl):
    """隔离中的标签金额与个数（被新规则拒绝满 TTL、尚未到原 due）。"""
    s = 0.0
    m = 0
    if ttl <= 0 or TK_i.shape[1] <= 4:
        return s, m
    for j in range(n):
        if TK_i[j, 2] == 1 and TK_i[j, 4] >= 0 and day >= TK_i[j, 4] + ttl and day < TK_i[j, 1] and TK_f[j] > 1e-15:
            s += TK_f[j]
            m += 1
    return s, m


@njit(cache=True)
def tk_quar_new(TK_f, TK_i, n, day, ttl):
    """当日（day）新进入隔离的标签个数（first_denied + ttl == day、早于原 due、仍有余额）。"""
    m = 0
    if ttl <= 0 or TK_i.shape[1] <= 4:
        return m
    for j in range(n):
        if TK_i[j, 2] == 1 and TK_i[j, 4] >= 0 and day == TK_i[j, 4] + ttl and day < TK_i[j, 1] and TK_f[j] > 1e-15:
            m += 1
    return m


@njit(cache=True)
def tk_deny(TK_f, TK_i, n, day, used_amt, deny_amt, ttl, mark_day):
    """按消费序（due 最早、ID 序；只看 day 可用标签）跳过 used_amt 后，把覆盖 deny_amt 的标签 first_denied 记为 mark_day（已有则不改；重复拒绝不重置）。返回新记个数。"""
    if not (deny_amt > 1e-12) or ttl <= 0 or TK_i.shape[1] <= 4:
        return 0
    m = 0
    idx = np.empty(n, np.int64)
    for j in range(n):
        if TK_i[j, 2] == 1 and TK_f[j] > 1e-15 and tk_ok(TK_i, j, day, ttl):
            idx[m] = j
            m += 1
    if m == 0:
        return 0
    key = np.empty(m)
    for k in range(m):
        j = idx[k]
        key[k] = TK_i[j, 1] * 1e12 + TK_i[j, 3]
    o = np.argsort(key, kind='mergesort')
    skip = used_amt
    left = deny_amt
    newm = 0
    for k in range(m):
        j = idx[o[k]]
        v = TK_f[j]
        if skip >= v - 1e-15:
            skip -= v
            continue
        rem = v - skip
        skip = 0.0
        if TK_i[j, 4] < 0:
            TK_i[j, 4] = mark_day
            newm += 1
        left -= rem
        if left <= 1e-12:
            break
    return newm


@njit(cache=True)
def tk_consume(TK_f, TK_i, n, day, amount, out_due, out_amt, ttl):
    """按 due 最早、ID 序消耗可用标签；返回段数（填 out_due / out_amt）。超额 / 非有限 → −1（双花拦截）。隔离中的标签不可消耗（ttl ≤ 0 时与 E6p 同式）。"""
    avail = tk_sum(TK_f, TK_i, n, day, True, ttl)
    if not np.isfinite(amount) or amount < 0.0 or amount > avail * (1.0 + 1e-12) + 1e-9:
        return -1
    k = 0
    left = min(amount, avail)
    while left > 1e-12:
        best = -1
        for j in range(n):
            if TK_i[j, 2] == 1 and tk_ok(TK_i, j, day, ttl) and TK_f[j] > 1e-15:
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
               fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig):
    """返回 (S_tot, S_early, R_buy, X_buy, D_buy, F, R_elig)。早退卖款按证券内早退请求占比分摊（DUE 先卖）。
    R_elig（E6q 路由）= 可由受限标签付款的常规买入（relig[s] = 1 的证券）；route_on = 0 时恒为 0、其余与 E6p 同式。"""
    S_tot = 0.0
    S_early = 0.0
    R_buy = 0.0
    X_buy = 0.0
    D_buy = 0.0
    R_elig = 0.0
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
            if route_on and relig[s] > 0.0:
                R_elig += bq * P * fr
        dn = abs(bq - sq) * P
        net_abs += dn
        if fb_on:
            fimp += fb_cost(dn, sig20[d, s], adv20[d, s], fbA, fbK, fbD, p0, V0)
    return S_tot, S_early, R_buy, X_buy, D_buy, c * net_abs + fimp, R_elig


@njit(cache=True)
def feasible(S_tot, S_early, R_buy, X_buy, D_buy, F, ordinary0, tk_usable, fund, lag, fsh_early, route_on, R_elig):
    """普通现金付常规买入、部署买入与全部费用；常规缺口与额外买入只能用可用标签（lag0 另含当日早退新标签）；部署不碰标签。
    E6q 路由（M1 / M2）：标签付常规买入的部分 min(缺口, 常规买) 不得超过合格常规买 R_elig（费用缺口照 E6p）；route_on = 0 时与 E6p 同式。"""
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
    if route_on:
        if min(need_tag, R_buy) > R_elig + 1e-9:
            return False, need_tag
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
def tl_add(TL_i, TL_f, S_i, d, s, lot_id, req, kind, side, qty, P, due, deadline, planned):
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
    if TL_i.shape[1] > 7:
        TL_i[r, 7] = deadline
    if TL_f.shape[1] > 4:
        TL_f[r, 4] = planned
    S_i[SI_NTL] = r + 1


@njit(cache=True)
def mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind, mk_i, mk_f):
    """mk_i = [half_on, m3_on, queue_days]、mk_f = [θ]（E6q）：M4 首次意向取剩余量 × θ 为固定目标（REARM 升级 = 余量全额）；
    M3 固定 first_decision 与 deadline = min(due, first_e + queue_days − 1)，当日目标量由收盘后的 M3 分配写入；全关时只多写 L_i[8] / L_f[4]（不参与 E6p 运算）。"""
    s = L_i[j, 0]
    L_i[j, 3] = LQ_EARLY
    L_i[j, 4] = d + 1
    if L_i.shape[1] > 8:
        if L_i[j, 8] < 0:
            L_i[j, 8] = d
        if mk_i[1] == 1:
            dl = d + mk_i[2]
            L_i[j, 9] = dl if dl < L_i[j, 2] else L_i[j, 2]
            L_i[j, 13] = 0
            L_f[j, 4] = 0.0
            if mk_i.shape[0] > 3 and mk_i[3] == 1:      # E6r GATE_REARM：REARM 定本次目标关闭量（L_f[5] = 待关闭量），M3 定每日分配（L_f[4]）
                if kind == KD_REARM:
                    L_i[j, 10] = 2
                    L_f[j, 5] = L_f[j, 0]
                else:
                    L_i[j, 10] = 1
                    L_f[j, 5] = mk_f[0] * L_f[j, 0]
                    S_i[SI_HALF] += 1
        elif mk_i[0] == 1:
            if kind == KD_REARM:
                L_i[j, 10] = 2
                L_f[j, 4] = L_f[j, 0]
            else:
                L_i[j, 10] = 1
                L_f[j, 5] = mk_f[0] * L_f[j, 0]
                L_f[j, 4] = L_f[j, 5]
                S_i[SI_HALF] += 1
        else:
            L_f[j, 4] = L_f[j, 0]
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
              ordinary0, tk_av, fund, lag, route_on, relig):
    """现金约束求解：全额可行则 (1,1,1)；否则先缩部署 zd；部署归零仍不可行 → E6o 原流程（先缩额外 zx，再缩常规 zr；zd 固定）。部署为零时与 E6o 同序同式。
    E6q：route_on 时 feasible 多一条路由约束（合格常规买）；route_on = 0 时与 E6p 同序同式。"""
    zr = 1.0
    zx = 1.0
    zd = 1.0
    S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, zr, zx, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                                    fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
    den = S_tot + R_b + X_b + D_b
    ok, need_tag = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
    err = 0
    if not ok and route_on:
        # 只因路由不可行（现金与标签总量够、但受限标签不可付不合格常规买）→ 只缩常规 zr（额外批次用标签，与此无关）；路由全通过时本分支不触发（与 E6p 同序）
        ok_nr, nn = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, False, R_el)
        if ok_nr:
            lo, hi = 0.0, 1.0
            for it in range(50):
                mid = 0.5 * (lo + hi)
                S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, mid, 1.0, 1.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                                buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
                den = S_tot + R_b + X_b + D_b
                okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
                if okm:
                    lo = mid
                else:
                    hi = mid
            S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, lo, 1.0, 1.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable,
                                                            ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
            den = S_tot + R_b + X_b + D_b
            ok, need_tag = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
            if ok:
                return lo, 1.0, 1.0, need_tag, 0
    if not ok:
        done = False
        if D_b > 0.0:
            S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, 1.0, 1.0, 0.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable,
                                                            ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
            den = S_tot + R_b + X_b + D_b
            okd, nd0 = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
            if okd:
                lo, hi = 0.0, 1.0
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, 1.0, 1.0, mid, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                                    buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
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
            S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, 1.0, 0.0, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable,
                                                            ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
            den = S_tot + R_b + X_b + D_b
            ok0, need0 = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
            if ok0:
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, 1.0, mid, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                                    buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr, zx = 1.0, lo
            else:
                zx = 0.0
                for it in range(50):
                    mid = 0.5 * (lo + hi)
                    S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, mid, 0.0, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable,
                                                                    buyable, ideal, c, fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
                    den = S_tot + R_b + X_b + D_b
                    okm, nm = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
                    if okm:
                        lo = mid
                    else:
                        hi = mid
                zr = lo
        S_tot, S_e, R_b, X_b, D_b, F, R_el = solve_eval(d, zr, zx, zd, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                                        fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, route_on, relig)
        den = S_tot + R_b + X_b + D_b
        ok, need_tag = feasible(S_tot, S_e, R_b, X_b, D_b, F, ordinary0, tk_av, fund, lag, F * S_e / den if den > 0 else 0.0, route_on, R_el)
        if not ok:
            # 缺口 ≤ 1e−6 元 = 普通现金在 0 附近的浮点残差（部署 / 缩量把现金压到 0 后的次日无卖出日），不当不可行（码 12，计数）；E6o 账户从未进入本分支
            err = 9 if need_tag > 1e-6 else 12
    return zr, zx, zd, need_tag, err


@njit(cache=True)
def ov_order(seed, d, svec, seckey):
    """E6R_BLOCK5_STABLE_SECURITY_V11 优先序：hash_u(路径种子, 五日块, 证券稳定键)（不用列号 / 行序 / 进程 hash）。"""
    blk = (d + 1) // 5
    m = svec.shape[0]
    key = np.empty(m)
    for i in range(m):
        key[i] = hash_u(seed, blk, seckey[svec[i]])
    return np.argsort(key, kind='mergesort')


@njit(cache=True)
def ov_cohort_rho(d, a, b, f_col, f_w, ov_lab, ov_st, ov_cell, ind, capsh, idev, rcap, lam, ovl, ernd, seed, seckey, x0s, rho_c, lab_c, keep_c):
    """入场随机在形成层重算本 cohort 的 ρ（与 e6r_overlay 同一 form_tilt；plan §8.1 LABEL_PROJECT / §8.2 JOINT 与 GATE_TILT 的随机门）。
    x0s[s] = 本快照常规 FLAT 票据（> 0 = 有票据；随机门的资格与计数口径 = 同快照真实动作）。GATE_TILT：真实门 = T0 BAD；随机门（JOINT / COUNT）同只数、
    （AMOUNT）同名义额末名部分，资格 = 已知状态且有票据（不删 UNKNOWN 凑数）。LABEL_PROJECT：非 NA 名字之间置换标签多重集（CELL 在格内）；
    TENOR：同式置换（只换 H 标签）。返回 (状态, 门掉只数, 门掉额)。"""
    m = b - a
    bf = np.empty(m)
    grp = np.empty(m, np.int64)
    u = np.full(m, rcap)
    sv = np.empty(m, np.int64)
    cells = np.empty(m, np.int64)
    for i in range(m):
        s = f_col[a + i]
        sv[i] = s
        bf[i] = f_w[a + i]
        grp[i] = ind[d, s]
        lab_c[i] = ov_lab[a + i]
        keep_c[i] = 1.0
        cells[i] = ov_cell[a + i]
    G = capsh.shape[1]
    gcap = np.empty(G)
    for g in range(G):
        gcap[g] = capsh[d, g] + idev
    ngate = 0
    vgate = 0.0
    if ovl == OV_GATETILT:
        nreal = 0
        vreal = 0.0
        for i in range(m):
            if ov_st[a + i] == 1 and x0s[sv[i]] > 0.0:
                nreal += 1
                vreal += x0s[sv[i]]
        if ernd == ER_JOINT or ernd == ER_GCOUNT or ernd == ER_GAMOUNT:
            ne = 0
            for i in range(m):
                if ov_st[a + i] >= 0 and x0s[sv[i]] > 0.0:
                    ne += 1
            el = np.empty(ne, np.int64)
            k = 0
            for i in range(m):
                if ov_st[a + i] >= 0 and x0s[sv[i]] > 0.0:
                    el[k] = i
                    k += 1
            o = ov_order(seed, d, sv[el], seckey)
            if ernd == ER_GAMOUNT:
                left = vreal
                for t in range(ne):
                    if left <= 1e-12 * (vreal if vreal > 1.0 else 1.0):
                        break
                    i = el[o[t]]
                    v = x0s[sv[i]]
                    if v <= left:
                        keep_c[i] = 0.0
                        left -= v
                        vgate += v
                    else:
                        keep_c[i] = 1.0 - left / v
                        vgate += left
                        left = 0.0
                    ngate += 1
            else:
                for t in range(min(nreal, ne)):
                    i = el[o[t]]
                    keep_c[i] = 0.0
                    ngate += 1
                    vgate += x0s[sv[i]]
        else:
            for i in range(m):
                if ov_st[a + i] == 1:
                    keep_c[i] = 0.0
                    if x0s[sv[i]] > 0.0:
                        ngate += 1
                        vgate += x0s[sv[i]]
    if ernd == ER_LABEL or ernd == ER_TENOR:
        # 非 NA 名字之间置换标签多重集（CELL：每个已知格内单独置换；其余 cohort 全域）；NA 集合不变
        if ovl == OV_CELL:
            order = np.argsort(cells, kind='mergesort')
            k0 = 0
            while k0 < m:
                c = cells[order[k0]]
                k1 = k0
                while k1 < m and cells[order[k1]] == c:
                    k1 += 1
                if c >= 0:
                    nn = 0
                    for t in range(k0, k1):
                        if lab_c[order[t]] != 0:
                            nn += 1
                    if nn > 1:
                        ix = np.empty(nn, np.int64)
                        ls = np.empty(nn, np.int64)
                        k = 0
                        for t in range(k0, k1):
                            if lab_c[order[t]] != 0:
                                ix[k] = order[t]
                                ls[k] = lab_c[order[t]]
                                k += 1
                        ls = np.sort(ls)
                        o = ov_order(seed, d, sv[ix], seckey)
                        for t in range(nn):
                            lab_c[ix[o[t]]] = ls[t]
                k0 = k1
        else:
            nn = 0
            for i in range(m):
                if lab_c[i] != 0:
                    nn += 1
            if nn > 1:
                ix = np.empty(nn, np.int64)
                ls = np.empty(nn, np.int64)
                k = 0
                for i in range(m):
                    if lab_c[i] != 0:
                        ix[k] = i
                        ls[k] = lab_c[i]
                        k += 1
                ls = np.sort(ls)
                o = ov_order(seed, d, sv[ix], seckey)
                for t in range(nn):
                    lab_c[ix[o[t]]] = ls[t]
    if ovl == OV_TILTH:
        for i in range(m):
            rho_c[i] = 1.0
        return KL_OK, ngate, vgate
    pin = np.zeros(m, np.bool_)
    for i in range(m):
        pin[i] = lab_c[i] == 0
    w = np.zeros(m)
    st = form_tilt(bf, lab_c, lam, u, grp, gcap, pin, keep_c, cells, ovl == OV_CELL, w)
    for i in range(m):
        bb = bf[i] * keep_c[i]
        rho_c[i] = w[i] / bb if bb > 0.0 else 0.0
    return st, ngate, vgate


@njit(cache=True)
def ov_apply(d, p0, p1, PB_i, PB_f, a, ov_rho, ov_lab, ov_st, ov_cell, ov_pin, seckey, expv, indsum, ind, capsh, idev, scap, NAVc, ovl, ernd,
             seed, nodes, rtv, S_i, DY, is_extra, labE_out, crho, rho_c, lab_c, keep_c):
    """账户层（plan §6.1 第二层）对一批票据 [p0, p1) 施加入场算子（x⁰ = PB_f 现值 = E6q 原式 FLAT 票据；expv / indsum = 本批提交前的共享残余）：
    GATE 删票不回填（随机 COUNT / AMOUNT：同快照真实删票只数 / 名义额，资格 = 已知测量且有票据）；TILT / CELL / GATE_TILT：先删门掉票据，
    q = x⁰·ρ 投影到同 B（单股余量 = scap·NAV − 已有、行业余量 = (份额 + 3pp)·NAV − 已有、NA 与零票据固定；CELL 每格预算 = Σ_cell x⁰）；
    TICKETS / JOINT：真实（或随机门后）would-be 票据在同名单非 NA 有票据名字之间求首个可行双射（CELL 在格内；失败 = 用真实票据见证并记状态）。
    labE_out[k] = 生效标签（TILT_H / TENOR 定 H，成交日志记标签）。统计写 DY（常规 / 额外两列组）。"""
    n = p1 - p0
    if n <= 0:
        return
    x0 = np.empty(n)
    rho = np.empty(n)
    keep = np.ones(n)
    labE = np.empty(n, np.int64)
    pin = np.zeros(n, np.bool_)
    cellv = np.empty(n, np.int64)
    sv = np.empty(n, np.int64)
    for i in range(n):
        k = p0 + i
        k2 = PB_i[k, 3]
        x0[i] = PB_f[k]
        sv[i] = PB_i[k, 0]
        rho[i] = ov_rho[k2]
        labE[i] = ov_lab[k2]
        pin[i] = ov_pin[k2]
        cellv[i] = ov_cell[k2]
        if crho:
            j = k2 - a
            rho[i] = rho_c[j]
            labE[i] = lab_c[j]
            keep[i] = keep_c[j]
            if ovl != OV_GATE:
                pin[i] = lab_c[j] == 0
        elif ovl == OV_GATETILT or ovl == OV_GATE:
            keep[i] = 1.0 if rho[i] > 0.0 else 0.0
    B0 = 0.0
    for i in range(n):
        B0 += x0[i]
    x = x0.copy()
    gn = 0
    gv = 0.0
    erst = 0
    capv = 0.0
    indv = 0.0
    nad = 0.0
    celld = 0.0
    nan_n = 0
    capb = 0
    indb = 0
    if ovl == OV_GATE:
        if ernd == ER_GCOUNT or ernd == ER_GAMOUNT:
            nreal = 0
            vreal = 0.0
            for i in range(n):
                if not (rho[i] > 0.0) and x0[i] > 0.0:
                    nreal += 1
                    vreal += x0[i]
            ne = 0
            for i in range(n):
                if (not pin[i]) and x0[i] > 0.0:
                    ne += 1
            el = np.empty(ne, np.int64)
            k = 0
            for i in range(n):
                if (not pin[i]) and x0[i] > 0.0:
                    el[k] = i
                    k += 1
            o = ov_order(seed, d, sv[el], seckey)
            if ernd == ER_GAMOUNT:
                left = vreal
                for t in range(ne):
                    if left <= 1e-12 * (vreal if vreal > 1.0 else 1.0):
                        break
                    i = el[o[t]]
                    if x0[i] <= left:
                        left -= x0[i]
                        gv += x0[i]
                        x[i] = 0.0
                    else:
                        x[i] = x0[i] - left
                        gv += left
                        left = 0.0
                    gn += 1
            else:
                for t in range(min(nreal, ne)):
                    i = el[o[t]]
                    gv += x0[i]
                    x[i] = 0.0
                    gn += 1
            DY[d, DY_ERSHORT] += gv - vreal              # 生成层 B 差 = 随机删票额 − 同快照真实删票额（COUNT 非零、AMOUNT ≈ 0）
        else:
            for i in range(n):
                if not (rho[i] > 0.0) and x0[i] > 0.0:
                    gv += x0[i]
                    x[i] = 0.0
                    gn += 1
    elif ovl == OV_TILT or ovl == OV_CELL or ovl == OV_GATETILT:
        x0g = np.empty(n)
        for i in range(n):
            x0g[i] = x0[i] * keep[i]
            if x0[i] > 0.0 and x0g[i] < x0[i]:
                gv += x0[i] - x0g[i]
                if x0g[i] == 0.0:
                    gn += 1
        u = np.empty(n)
        grp = np.empty(n, np.int64)
        for i in range(n):
            s = sv[i]
            r_ = scap * NAVc - expv[s]
            u[i] = r_ if r_ > x0g[i] else x0g[i]
            grp[i] = ind[d, s]
        G = capsh.shape[1]
        gcap = np.empty(G)
        for g in range(G):
            r_ = (capsh[d, g] + idev) * NAVc - indsum[g]
            gcap[g] = r_ if r_ > 0.0 else 0.0
        gb = np.zeros(G)
        for i in range(n):
            if grp[i] >= 0:
                gb[grp[i]] += x0g[i]
        for g in range(G):
            if gb[g] > gcap[g]:
                gcap[g] = gb[g]                    # 计划层可行性：x⁰ 已满足（E6q 原式），舍入级超出放宽到 x⁰ 本身
        pinA = np.empty(n, np.bool_)
        for i in range(n):
            pinA[i] = pin[i] or x0g[i] == 0.0
            if pin[i] and x0g[i] > 0.0:
                nan_n += 1
        xr = np.zeros(n)
        st = transport_cells(x0g, rho, u, grp, gcap, pinA, cellv, ovl == OV_CELL, xr)
        if st != KL_OK:
            S_i[SI_PROJF] += 1
            DY[d, DY_OVST] = st
            for i in range(n):
                xr[i] = x0g[i]
        for i in range(n):
            x[i] = xr[i]
        xpre = x.copy()
        if ernd == ER_TICKETS or ernd == ER_JOINT:
            # 首个可行双射：域 = 非固定、有票据的名字；CELL 逐格（格预算自动守住）；其余全域（行业余量 = gcap − 固定名字占用）
            gl = gcap.copy()
            for i in range(n):
                if pinA[i] and grp[i] >= 0:
                    gl[grp[i]] -= x[i]
            for g in range(G):
                if gl[g] < 0.0:
                    gl[g] = 0.0
            if ovl == OV_CELL:
                ncell = 0
                corder = np.argsort(cellv, kind='mergesort')
                k0 = 0
                all_id = True
                any_lim = False
                any_nom = False
                xn = x.copy()
                while k0 < n:
                    c = cellv[corder[k0]]
                    k1 = k0
                    while k1 < n and cellv[corder[k1]] == c:
                        k1 += 1
                    if c >= 0:
                        nd = 0
                        for t in range(k0, k1):
                            i = corder[t]
                            if (not pinA[i]) and x[i] > 0.0:
                                nd += 1
                        if nd > 1:
                            dom = np.empty(nd, np.int64)
                            k = 0
                            for t in range(k0, k1):
                                i = corder[t]
                                if (not pinA[i]) and x[i] > 0.0:
                                    dom[k] = i
                                    k += 1
                            tk = np.empty(nd)
                            for t in range(nd):
                                tk[t] = x[dom[t]]
                            to = np.argsort(-tk, kind='mergesort')
                            tick = tk[to]
                            ccap = np.empty(nd)
                            cg = np.full(nd, -1, np.int64)
                            for t in range(nd):
                                ccap[t] = u[dom[t]]
                            o = ov_order(seed, d, sv[dom], seckey)
                            g2 = np.zeros(1)
                            assign, rst, nn_ = rt_dispatch(tick, ccap, cg, g2, o, nodes, rtv, to, S_i)
                            DY[d, DY_ERNODES] += nn_
                            ncell += 1
                            if rst == RTS_FEASIBLE:
                                for t in range(nd):
                                    xn[dom[assign[t]]] = tick[t]
                            elif rst == RTS_LIMIT:
                                any_lim = True
                            else:
                                any_nom = True
                    k0 = k1
                same = True
                for i in range(n):
                    if xn[i] != x[i]:
                        same = False
                if any_lim:
                    erst = 3
                    S_i[SI_ERLIM] += 1
                elif any_nom:
                    erst = 2
                    S_i[SI_ERNOM] += 1
                elif same:
                    erst = 4
                    S_i[SI_ERID] += 1
                else:
                    erst = 1
                    S_i[SI_ERFEAS] += 1
                if not (any_lim or any_nom):
                    for i in range(n):
                        x[i] = xn[i]
            else:
                nd = 0
                for i in range(n):
                    if (not pinA[i]) and x[i] > 0.0:
                        nd += 1
                if nd > 1:
                    dom = np.empty(nd, np.int64)
                    k = 0
                    for i in range(n):
                        if (not pinA[i]) and x[i] > 0.0:
                            dom[k] = i
                            k += 1
                    tk = np.empty(nd)
                    for t in range(nd):
                        tk[t] = x[dom[t]]
                    to = np.argsort(-tk, kind='mergesort')
                    tick = tk[to]
                    ccap = np.empty(nd)
                    cg = np.empty(nd, np.int64)
                    for t in range(nd):
                        ccap[t] = u[dom[t]]
                        cg[t] = grp[dom[t]]
                    o = ov_order(seed, d, sv[dom], seckey)
                    g2 = gl.copy()
                    assign, rst, nn_ = rt_dispatch(tick, ccap, cg, g2, o, nodes, rtv, to, S_i)
                    DY[d, DY_ERNODES] += nn_
                    if rst == RTS_FEASIBLE:
                        xn = x.copy()
                        for t in range(nd):
                            xn[dom[assign[t]]] = tick[t]
                        same = True
                        for i in range(n):
                            if xn[i] != x[i]:
                                same = False
                        if same:
                            erst = 4
                            S_i[SI_ERID] += 1
                        else:
                            erst = 1
                            S_i[SI_ERFEAS] += 1
                        for i in range(n):
                            x[i] = xn[i]
                    elif rst == RTS_LIMIT:
                        erst = 3
                        S_i[SI_ERLIM] += 1
                    else:
                        erst = 2
                        S_i[SI_ERNOM] += 1
                else:
                    erst = 5                               # 结构性退化（≤ 1 个可换名字）
                    S_i[SI_ERID] += 1
        if ernd == ER_TICKETS or ernd == ER_JOINT or ernd == ER_LABEL:
            # 随机票据与同快照 would-be 真实票据的 Σw / Σw² 相对差（TICKETS / JOINT = 多重集置换应为 0；LABEL_PROJECT 只保 Σw，Σw² 照报）
            if ernd == ER_LABEL:
                kr = np.ones(n)
                rr_ = np.empty(n)
                pr_ = np.empty(n, np.bool_)
                for i in range(n):
                    k2 = PB_i[p0 + i, 3]
                    rr_[i] = ov_rho[k2]
                    pr_[i] = ov_pin[k2]
                    if ovl == OV_GATETILT and not (rr_[i] > 0.0):
                        kr[i] = 0.0
                x0r = np.empty(n)
                pinr = np.empty(n, np.bool_)
                for i in range(n):
                    x0r[i] = x0[i] * kr[i]
                    pinr[i] = pr_[i] or x0r[i] == 0.0
                xreal = np.zeros(n)
                st2 = transport_cells(x0r, rr_, u, grp, gcap, pinr, cellv, ovl == OV_CELL, xreal)
                if st2 == KL_OK:
                    for i in range(n):
                        xpre[i] = xreal[i]
            s1a = 0.0
            s1b = 0.0
            s2a = 0.0
            s2b = 0.0
            for i in range(n):
                s1a += xpre[i]
                s1b += x[i]
                s2a += xpre[i] * xpre[i]
                s2b += x[i] * x[i]
            dw_ = abs(s1b - s1a) / s1a if s1a > 0.0 else 0.0
            dw2_ = abs(s2b - s2a) / s2a if s2a > 0.0 else 0.0
            if dw_ > DY[d, DY_ERDW]:
                DY[d, DY_ERDW] = dw_
            if dw2_ > DY[d, DY_ERDW2]:
                DY[d, DY_ERDW2] = dw2_
        # 违约与漂移（计划层；相对 NAV）
        for i in range(n):
            if x[i] > u[i]:
                v_ = (x[i] - u[i]) / NAVc
                if v_ > capv:
                    capv = v_
            if u[i] > 0.0 and x[i] >= u[i] * (1.0 - 1e-12) and x[i] > 0.0:
                capb += 1
            if pinA[i]:
                dd_ = abs(x[i] - x0g[i])
                if dd_ > nad:
                    nad = dd_
        gs2 = np.zeros(G)
        for i in range(n):
            if grp[i] >= 0:
                gs2[grp[i]] += x[i]
        for g in range(G):
            if gs2[g] > gcap[g]:
                v_ = (gs2[g] - gcap[g]) / NAVc
                if v_ > indv:
                    indv = v_
            if gcap[g] > 0.0 and gs2[g] >= gcap[g] * (1.0 - 1e-12) and gs2[g] > 0.0:
                indb += 1
        if ovl == OV_CELL:
            corder = np.argsort(cellv, kind='mergesort')
            k0 = 0
            while k0 < n:
                c = cellv[corder[k0]]
                k1 = k0
                s0_ = 0.0
                s1_ = 0.0
                while k1 < n and cellv[corder[k1]] == c:
                    s0_ += x0g[corder[k1]]
                    s1_ += x[corder[k1]]
                    k1 += 1
                if c >= 0 and abs(s1_ - s0_) > celld:
                    celld = abs(s1_ - s0_)
                k0 = k1
    elif ovl == OV_TILTH:
        if ernd == ER_TENOR:
            erst = 1
    # 写回与统计
    act = 0.0
    trf = 0.0
    X = 0.0
    for i in range(n):
        if x[i] != x0[i]:
            act = 1.0
        if x[i] > x0[i]:
            trf += x[i] - x0[i]
        PB_f[p0 + i] = x[i]
        labE_out[p0 + i] = labE[i]
        X += x[i]
    if is_extra:
        DY[d, DY_OVXB] += B0
        DY[d, DY_OVXX] += X
    else:
        DY[d, DY_OVB] = B0
        DY[d, DY_OVX] = X
        DY[d, DY_OVACT] = act
        DY[d, DY_OVTRF] = trf
        DY[d, DY_ERST] = erst
        DY[d, DY_ERID] = 1.0 if erst == 4 or erst == 5 else 0.0
    if erst > 0:
        DY[d, DY_ERC1 + erst - 1] += 1.0
    DY[d, DY_OVGN] += gn
    DY[d, DY_OVGV] += gv
    if capv > DY[d, DY_OVCAPV]:
        DY[d, DY_OVCAPV] = capv
    if indv > DY[d, DY_OVINDV]:
        DY[d, DY_OVINDV] = indv
    DY[d, DY_OVNAN] += nan_n
    if nad > DY[d, DY_OVNAD]:
        DY[d, DY_OVNAD] = nad
    if celld > DY[d, DY_OVCELLD]:
        DY[d, DY_OVCELLD] = celld
    DY[d, DY_CAPBN] += capb
    DY[d, DY_INDBN] += indb


@njit(cache=True)
def step(d0, d1, ip, fp,
         pv, pc, pcobs, cvr, cpct, trig, t1a, lvl, sellable, buyable, isopen, sig20, adv20, zsz, ind, capsh, bench, pvage, iskid,
         nclean, tgt_expo,
         f_ptr, f_col, f_w, u_ptr, u_col, n_ptr, n_col, nf_ptr, nf_col,
         tg_amt, tg_cnt, tg_isk, tg_re, p_bern, tg_cancel, tg_b, tg_isk2, tg_aisk, tg_rchk,
         L_i, L_f, L_id, q, ep_until, ep_clear, last_exit_due, first_held,
         TK_f, TK_i, LK_f, LK_i, PB_i, PB_f, S_f, S_i, IN_i, IN_f, DY, HOLDH, LOTH, RISK, HITS, TL_i, TL_f, DBG,
         ov_rho, ov_lab, ov_lab20, ov_st, ov_cell, ov_pin, seckey, PL_i, PL_f):
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
    # ---- E6q 开关（全关 = E6p）
    m1 = ip[IP_M1] == 1
    m2 = ip[IP_M2] == 1
    m3 = ip[IP_M3] == 1
    half = ip[IP_HALF] == 1
    rearm = ip[IP_REARM] == 1
    qdays = ip[IP_QDAYS]
    route_on = ip[IP_ROUTE] == 1
    rtm = ip[IP_RT]
    fhit = ip[IP_FIRSTHIT] == 1
    nodes = ip[IP_NODES]
    rtv = ip[IP_RTV]
    ttl = qdays if (m1 or m2) else 0
    pstar = fp[FP_PSTAR]
    aref = fp[FP_AREF]
    theta = fp[FP_THETA]
    gate = m3 or half
    unit_cny = aref / V0 if aref > 0.0 else 0.0           # 引擎单位 → 人民币（A_design,T = A_ref · NAV_T / NAV_0；固定路径与反馈账户同式）
    # ---- E6r 开关（全关 = E6q）
    ovl = ip[IP_OVL]
    ernd = ip[IP_ERND]
    gr = ip[IP_GR] == 1
    lam = fp[FP_LAMBDA]
    rcap = fp[FP_RCAP]
    mk_i = np.zeros(4, np.int64)
    mk_i[0] = 1 if half else 0
    mk_i[1] = 1 if m3 else 0
    mk_i[2] = qdays
    mk_i[3] = 1 if gr else 0
    ov_x0 = np.zeros(N)                                   # E6r：本快照常规 FLAT 票据（随机门的资格 / 计数口径）
    pb_x0 = np.zeros(PB_f.shape[0])                       # E6r：每张计划票据施加算子前的 x⁰
    pb_lab = np.zeros(PB_f.shape[0], np.int64)            # E6r：每张计划票据的生效标签
    rho_c = np.zeros(8192)                                # E6r：随机路径形成层重算的 cohort ρ / 标签 / 保留比例
    lab_c = np.zeros(8192, np.int64)
    keep_c = np.ones(8192)
    ov_indtmp = np.zeros(capsh.shape[1])
    hv_ = np.zeros(N)                                     # E6r：收盘逐证券市值累加（实际持仓层集中度）
    hl_ = np.zeros(N, np.int64)
    mk_f = np.zeros(1)
    mk_f[0] = theta
    relig = np.zeros(N)
    regbuy = np.zeros(N)
    sellfix = np.zeros(N)
    capx = np.full(N, np.inf)
    isnew = np.zeros(N, np.bool_)
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
                rq = L_f[j, 0]
                if gate and L_i[j, 3] == LQ_EARLY and d < L_i[j, 2]:   # E6q M3 / M4：当日目标量（到原 due 起全量）
                    a_ = L_f[j, 4]
                    if a_ < rq:
                        rq = a_ if a_ > 0.0 else 0.0
                S_req[s] += rq
                if L_i[j, 3] == LQ_EARLY and d < L_i[j, 2]:      # 只算仍早于原 due 的早退（迟到成交不生标签）
                    S_early_req[s] += rq
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
                if route_on and PB_i[k, 2] == 1:
                    relig[s] = 1.0
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
        tk_av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True, ttl)
        tag_all = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, False, ttl)
        lk_all = tk_sum(LK_f, LK_i, S_i[SI_NLK], d, False, 0)
        ordinary0 = cash0 - tag_all - lk_all
        zr, zx, zd, need_tag, err9 = solve_all(d, 1.0, nt, tlist, pv, S_req, B_r, B_x, B_d, S_early_req, isopen, sellable, buyable, ideal, c,
                                               fb_on, sig20, adv20, fbA, fbK, fbD, p0, V0, ordinary0, tk_av, fund, lag, route_on, relig)
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
        s10 = 0.0
        half_done = 0
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
                kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, need_tag, seg_due, seg_amt, ttl)
                if kk < 0:
                    if err9 == 12:                     # 舍入级缺口：只消耗实际可用标签，不报错
                        av0 = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True, ttl)
                        kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(need_tag, av0), seg_due, seg_amt, ttl)
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
                        if L_i[j, 7] == 1 and L_i[j, 3] == want and L_f[j, 0] > 0.0 and \
                                (not gate or want != LQ_EARLY or d >= L_i[j, 2] or L_f[j, 4] > 1e-15):
                            if best < 0 or L_i[j, 2] < L_i[best, 2] or (L_i[j, 2] == L_i[best, 2] and L_id[j] < L_id[best]):
                                best = j
                        j = nxt[j]
                    if best < 0:
                        break
                    gated = gate and want == LQ_EARLY and d < L_i[best, 2]
                    vcap = L_f[best, 0]
                    tgt0 = L_f[best, 4] if gated else np.nan
                    if gated and L_f[best, 4] < vcap:
                        vcap = L_f[best, 4]
                    if full or left >= vcap * (1.0 - 1e-9):
                        v = vcap
                    else:
                        v = left
                    L_f[best, 0] -= v
                    if L_f[best, 0] < 0.0:
                        L_f[best, 0] = 0.0
                    if gated:
                        L_f[best, 4] -= v
                        if L_f[best, 4] < 0.0:
                            L_f[best, 4] = 0.0
                        if gr:                                 # E6r GATE_REARM：待关闭量同步扣减（当日分配 ≤ 待关闭量）
                            L_f[best, 5] -= v
                            if L_f[best, 5] < 0.0:
                                L_f[best, 5] = 0.0
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
                            if half and L_i[best, 10] == 1:
                                okind = OK_EXIT_HALF
                            elif half and L_i[best, 10] == 2:
                                okind = OK_EXIT_REARM
                            if m3 and L_i[best, 13] == 1:
                                okind = OK_DEADLINE
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[best], rr, okind, 1, v, P, L_i[best, 2], L_i[best, 9] if m3 else -1,
                               tgt0 * pc[d - 1, s] if (gated and d >= 1) else np.nan)
                        tl_lab(TL_i, TL_f, S_i, L_i[best, 14], L_i[best, 15], L_i[best, 16], L_i[best, 17], 0.0, 0.0)
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
                    elif gated and half and ((L_f[best, 5] <= 1e-15) if gr else (L_f[best, 4] <= 1e-15)):
                        # E6q M4：首次半量目标完成 → 余半回持有、due 不变、不再开 episode（REARM 升级另由收盘观察处理）
                        L_i[best, 3] = LQ_NONE
                        L_i[best, 4] = -1
                        L_i[best, 6] = -1
                        half_done += 1
                        if rr >= 0:
                            IN_i[rr, IN_EXEC] = d
                            IN_i[rr, IN_STATUS] = 1
                            n_exit_early += 1
                            hd = d - L_i[best, 1]
                            HOLDH[min(max(hd, 0), HOLDH.shape[0] - 1)] += 1
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
                hh = PL_i[s, 4] if (ovl == OV_TILTH and PL_i[s, 5] == 1) else H     # E6r TILT_H：当日新批次 due = e0 + 分配 H
                if qr > 1e-15:
                    nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + hh, P, sig20[d, s], 0, qr)
                    lot_lab(L_i, nj, PL_i, s)
                    DY[d, DY_PAIDR] += qr * P
                    if tlog and nj >= 0:
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_REGULAR, 0, qr, P, d + hh, -1, B_r[s])
                        pw_ = B_r[s] / Vprev0 if Vprev0 > 0.0 else 0.0
                        tl_lab(TL_i, TL_f, S_i, PL_i[s, 0], PL_i[s, 1], PL_i[s, 2], PL_i[s, 3], PL_f[s, 0], pw_)
                if qx > 1e-15:
                    x_exec += qx * P
                    DY[d, DY_PAIDX] += qx * P
                    if remain and fund == FD_NATIVE:
                        kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, qx * P, seg_due, seg_amt, ttl)
                        if kk < 0:
                            S_i[SI_ERR] = 4
                            nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 1, qx)
                            if tlog and nj >= 0:
                                tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qx, P, d + H, -1, B_x[s])
                        else:
                            for k3 in range(kk):
                                due3 = seg_due[k3] if seg_due[k3] >= d + 1 else d + 1
                                nj = new_lot(L_i, L_f, L_id, S_i, s, d, due3, P, sig20[d, s], 2, seg_amt[k3] / P)
                                if tlog and nj >= 0:
                                    tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, seg_amt[k3] / P, P, due3, -1, B_x[s])
                    else:
                        nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + hh, P, sig20[d, s], 1, qx)
                        lot_lab(L_i, nj, PL_i, s)
                        if tlog and nj >= 0:
                            tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qx, P, d + hh, -1, B_x[s])
                            pw_ = B_x[s] / Vprev0 if Vprev0 > 0.0 else 0.0
                            tl_lab(TL_i, TL_f, S_i, PL_i[s, 0], PL_i[s, 1], PL_i[s, 2], PL_i[s, 3], PL_f[s, 0], pw_)
                if qd > 1e-15:
                    x_dep += qd * P
                    nj = new_lot(L_i, L_f, L_id, S_i, s, d, d + H, P, sig20[d, s], 3, qd)
                    if tlog and nj >= 0:
                        tl_add(TL_i, TL_f, S_i, d, s, L_id[nj], -1, OK_EXTRA, 0, qd, P, d + H, -1, B_d[s])
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
                        s10 += (dn / Vprev0) * sg * sp0 * (dn / (V0 * av * p0))
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
            av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True, ttl)
            kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(need_tag, av), seg_due, seg_amt, ttl)
            used_reg = min(need_tag, av)
        used_ext = 0.0
        if x_exec > 1e-12 and not (remain and fund == FD_NATIVE) and (fund == FD_NATIVE or fund == FD_NEXT):
            av = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, True, ttl)
            if x_exec > av + 1e-7 * max(1.0, V_pre):
                S_i[SI_ERR] = 6
            kk = tk_consume(TK_f, TK_i, S_i[SI_NTK], d, min(x_exec, av), seg_due, seg_amt, ttl)
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
        DY[d, DY_S10] = s10
        DY[d, DY_HALFDN] = half_done
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
            relig[s] = 0.0
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
        if NAVc > 0.0:                                   # E6r：实际持仓层集中度（逐证券市值 / NAV；只记录）
            nh_ = 0
            for j in range(nl):
                if L_i[j, 7] == 1 and L_f[j, 0] > 0.0:
                    s = L_i[j, 0]
                    if hv_[s] == 0.0:
                        hl_[nh_] = s
                        nh_ += 1
                    hv_[s] += L_f[j, 0] * pc[d, s]
            h2_ = 0.0
            h15_ = 0.0
            for k in range(nh_):
                s = hl_[k]
                w_ = hv_[s] / NAVc
                if w_ > 0.0:
                    h2_ += w_ * w_
                    h15_ += w_ ** 1.5
                hv_[s] = 0.0
            DY[d, DY_AHH2] = h2_
            DY[d, DY_AHH15] = h15_
        DY[d, 16] = tk_sum(TK_f, TK_i, S_i[SI_NTK], d, False, ttl)
        DY[d, 26] = tk_sum(LK_f, LK_i, S_i[SI_NLK], d, False, 0)
        DY[d, DY_CASHC] = S_f[SF_CASH]
        if ttl > 0:
            DY[d, DY_TKU] = tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, True, ttl)
            qa_, qn_ = tk_quar(TK_f, TK_i, S_i[SI_NTK], d + 1, ttl)
            DY[d, DY_TKQ] = qa_
            DY[d, DY_NTKQ] = qn_
            S_i[SI_QUAR] += tk_quar_new(TK_f, TK_i, S_i[SI_NTK], d + 1, ttl)
        else:
            DY[d, DY_TKU] = tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, True, 0)
        S_f[SF_LOCKDAYS] += DY[d, 16] + DY[d, 26]
        if d + 1 >= T:
            continue
        n_int_today = 0
        for k in range(N):
            sec_new_int[k] = False
            sec_due_max[k] = -1
        nrisk = 0
        if not (shadow and fhit):
            for j in range(nl):
                if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2]:
                    nrisk += 1
                    RISK[d, min(d - L_i[j, 1], NL - 1)] += 1
        DY[d, 33] = nrisk
        # ---- E6q M4 REARM：首次半量之后（含半量未成交期间）逐日观察已知状态；已知 False → has_cleared；之后 True → 同一请求提到余量（UNKNOWN 不解除；θ = 0 不卖）
        if half and rearm and exit_on and not shadow and theta > 0.0:
            nre = 0
            for j in range(nl):
                if L_i[j, 7] != 1 or L_i[j, 10] != 1 or L_f[j, 0] <= 0.0 or L_i[j, 8] >= d or not (d + 1 < L_i[j, 2]):
                    continue
                v = trig[d, L_i[j, 0]]
                if v == 0:
                    L_i[j, 11] = 1
                elif v == 1 and L_i[j, 11] == 1:
                    nre += 1
                    S_i[SI_REARMN] += 1
                    if L_i[j, 3] == LQ_NONE:
                        n_int_today += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                                  t1a, lvl, recon, u_ptr, u_col, KD_REARM, mk_i, mk_f)
                    elif gr:
                        # E6r GATE_REARM：待处理中升级 = 同一请求提到当前余量；deadline 不续、不叠卖（当日分配由下方 M3 块重算）
                        L_i[j, 10] = 2
                        L_f[j, 5] = L_f[j, 0]
                        DY[d, DY_GRPROM] += 1
                    else:
                        L_i[j, 10] = 2
                        L_f[j, 4] = L_f[j, 0]
            DY[d, DY_REARM] = nre
        if exit_on or shadow:
            if smode == SM_REAL or shadow:
                nhs = 0
                for j in range(nl):
                    if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
                        continue
                    if half and L_i[j, 10] >= 1:              # E6q M4：已开 episode 的余半不再开新 episode（持续 LEVEL 不几何减半）
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
                    if shadow and fhit:
                        # E6q 首达影子：每批只记首次已知 True；风险 = 未首达、信号已知、次日执行 < due（UNKNOWN 既非事件也非风险）
                        if L_i[j, 12] == 1 or unk:
                            continue
                        lay = min(d - L_i[j, 1], NL - 1)
                        RISK[d, lay] += 1
                        nrisk += 1
                        if hit:
                            HITS[d, lay] += 1
                            L_i[j, 12] = 1
                        continue
                    if unk:
                        S_i[SI_UNKDAYS] += 1
                    if not hit:
                        continue
                    if shadow:
                        HITS[d, min(d - L_i[j, 1], NL - 1)] += 1
                        continue
                    if half and not (theta > 0.0):
                        continue
                    n_int_today += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max,
                                              t1a, lvl, recon, u_ptr, u_col, KD_TRIG, mk_i, mk_f)
                    if half:
                        nhs += 1
                if shadow and fhit:
                    DY[d, 33] = nrisk
                DY[d, DY_HALFST] = nhs
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
            elif smode == SM_TLR:
                # E6r T1A_TIME_LEVEL_RANK：本账户当日状态下 T1a 会产生的合法意向名义额（按日龄桶；与触发标记同一批次资格）→ 本账户 R_INTENT 按当日
                # cvr_pct 降序（LEVEL 坏度）选额，末批部分（select_v2 LVL2 同式；不借他账户未来成交）
                for kb in range(NB):
                    tg_b[d, kb] = 0.0
                amt_ = 0.0
                for j in range(nl):
                    if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]) or not (L_f[j, 0] > 0.0):
                        continue
                    s = L_i[j, 0]
                    if t1a[d, s] == 1:
                        v_ = L_f[j, 0] * pc[d, s]
                        tg_b[d, bucket_of(d + 1 - L_i[j, 1])] += v_
                        amt_ += v_
                DY[d, DY_TLRAMT] = amt_
                if amt_ > 1e-12:
                    n_int_today += select_v2(d, SM_LVL2, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
                                             tg_b, tg_isk2, tg_aisk, sec_new_int, sec_due_max, DY, mk_i, mk_f)
            elif smode >= SM_AMT2 and smode != SM_RCHK:
                n_int_today += select_v2(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
                                         tg_b, tg_isk2, tg_aisk, sec_new_int, sec_due_max, DY, mk_i, mk_f)
            elif smode == SM_BERN:
                n_int_today += select_bern(d, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, p_bern,
                                           sec_new_int, sec_due_max, mk_i, mk_f, fhit)
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
                                     t1a, lvl, recon, u_ptr, u_col, KD_RENEW, mk_i, mk_f)
            if smode == SM_RCHK and tg_rchk[d] > 1e-12:
                rq += select_rchk(d, seed, NL, renew, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, tg_rchk[d],
                                  sec_new_int, sec_due_max, DY, mk_i, mk_f)
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
        for k in range(S_i[SI_NPB]):                     # E6r：昨日计划的逐证券标签已在今日成交时读完
            PL_i[PB_i[k, 0], 5] = 0
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
            PB_i[npb, 3] = k2
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
        # ---- E6r 入场算子（常规批次）：x⁰ = 上面 E6q 原式 FLAT 票据；提交前按算子改票据（共享残余 = 提交前 expv / indsum）
        crho = False
        if ovl != OV_NONE:
            DY[d, DY_OVCN] = b - a
            gsum_ = 0.0
            nt1_ = 0
            nt3_ = 0
            for k2 in range(a, b):
                gsum_ += f_w[k2]
                if ov_lab[k2] == 1:
                    nt1_ += 1
                elif ov_lab[k2] == 3:
                    nt3_ += 1
            DY[d, DY_OVG] = gsum_
            DY[d, DY_NT1] = nt1_
            DY[d, DY_NT3] = nt3_
            for k in range(npb):
                pb_x0[k] = PB_f[k]
            crho = ernd == ER_LABEL or ernd == ER_TENOR or ernd == ER_JOINT or (ovl == OV_GATETILT and (ernd == ER_GCOUNT or ernd == ER_GAMOUNT))
            if crho and b > a:
                for k in range(npb):
                    ov_x0[PB_i[k, 0]] = PB_f[k]
                stc, ngc, vgc = ov_cohort_rho(d, a, b, f_col, f_w, ov_lab, ov_st, ov_cell, ind, capsh, idev, rcap, lam, ovl, ernd, seed, seckey,
                                              ov_x0, rho_c, lab_c, keep_c)
                if stc != KL_OK:
                    S_i[SI_PROJF] += 1
                    DY[d, DY_OVST] = stc
                for k in range(npb):
                    ov_x0[PB_i[k, 0]] = 0.0
            crho_on = crho and b > a
            ov_apply(d, 0, npb, PB_i, PB_f, a, ov_rho, ov_lab, ov_st, ov_cell, ov_pin, seckey, expv, indsum, ind, capsh, idev, scap, NAVc, ovl, ernd,
                     seed, nodes, rtv, S_i, DY, False, pb_lab, crho_on, rho_c, lab_c, keep_c)
            hs_ = 0.0
            for k in range(npb):
                s = PB_i[k, 0]
                k2 = PB_i[k, 3]
                lb = pb_lab[k]
                hh = H
                if ovl == OV_TILTH:
                    hh = 30 if lb == 1 else (20 if lb == 2 else (10 if lb == 3 else H))
                hs_ += hh
                PL_i[s, 0] = d
                PL_i[s, 1] = lb
                PL_i[s, 2] = ov_lab20[k2]
                PL_i[s, 3] = ov_st[k2]
                PL_i[s, 4] = hh
                PL_i[s, 5] = 1
                PL_f[s, 0] = f_w[k2]
                rho_eff = ov_rho[k2]
                if crho_on:
                    rho_eff = keep_c[k2 - a] * rho_c[k2 - a]
                PL_f[s, 1] = f_w[k2] * rho_eff
                PL_f[s, 2] = PB_f[k]
                PL_f[s, 3] = pb_x0[k]
                PL_f[s, 4] = 0.0
                PL_f[s, 5] = 0.0
            DY[d, DY_HMEAN] = hs_ / npb if npb > 0 else 0.0
        else:
            for k in range(npb):
                s = PB_i[k, 0]
                k2 = PB_i[k, 3]
                PL_i[s, 0] = d
                PL_i[s, 1] = ov_lab[k2]
                PL_i[s, 2] = ov_lab20[k2]
                PL_i[s, 3] = ov_st[k2]
                PL_i[s, 4] = H
                PL_i[s, 5] = 1
                PL_f[s, 0] = f_w[k2]
                PL_f[s, 1] = f_w[k2]
                PL_f[s, 2] = PB_f[k]
                PL_f[s, 3] = PB_f[k]
                PL_f[s, 4] = 0.0
                PL_f[s, 5] = 0.0
        pg_ = 0.0
        ph2_ = 0.0
        ph15_ = 0.0
        for k in range(npb):
            s = PB_i[k, 0]
            expv[s] += PB_f[k]
            g = ind[d, s]
            if g >= 0:
                indsum[g] += PB_f[k]
            if NAVc > 0.0 and PB_f[k] > 0.0:
                wk = PB_f[k] / NAVc
                pg_ += wk
                ph2_ += wk * wk
                ph15_ += wk ** 1.5
        DY[d, DY_PAG] = pg_
        DY[d, DY_PAH2] = ph2_
        DY[d, DY_PAH15] = ph15_
        DY[d, 23] = 0.0
        # ---- E6q 次日固定净单（T 收盘价估值）：常规计划买 − 到期卖（及 M2 下的 NATIVE 全量早退卖）；M2 / M3 预算、路由合格标志用
        if m2 or m3 or route_on:
            regbuy[:] = 0.0
            sellfix[:] = 0.0
            for k in range(npb):
                regbuy[PB_i[k, 0]] += PB_f[k]
            for j in range(nl):
                if L_i[j, 7] != 1 or not (L_f[j, 0] > 0.0):
                    continue
                s = L_i[j, 0]
                isdue = L_i[j, 3] == LQ_DUE or (L_i[j, 3] == LQ_NONE and L_i[j, 2] <= d + 1) or (L_i[j, 3] == LQ_EARLY and L_i[j, 2] <= d + 1)
                if isdue or (L_i[j, 3] == LQ_EARLY and not m3):
                    sellfix[s] += L_f[j, 0] * pc[d, s]
            if m2 or m3:
                for k2 in range(a, b):
                    s = f_col[k2]
                    av = adv20[d, s]
                    if np.isfinite(av) and av > 0.0 and unit_cny > 0.0 and np.isfinite(pstar):
                        capx[s] = pstar * av / unit_cny
                    else:
                        capx[s] = np.inf
        # ---- E6q M3：信息卖单证券净单预算分配（队列 deadline, first_decision, lot；到 deadline 强制；p* → ∞ = 全量 = NATIVE）
        if m3 and exit_on and not shadow:
            m3n = 0
            for j in range(nl):
                if L_i[j, 7] == 1 and L_i[j, 3] == LQ_EARLY and L_f[j, 0] > 0.0 and d + 1 < L_i[j, 2]:
                    m3n += 1
            if m3n > 0:
                cand = np.empty(m3n, np.int64)
                ck = np.empty(m3n, np.int64)
                m = 0
                for j in range(nl):
                    if L_i[j, 7] == 1 and L_i[j, 3] == LQ_EARLY and L_f[j, 0] > 0.0 and d + 1 < L_i[j, 2]:
                        cand[m] = j
                        dlr = L_i[j, 9] - d + 8
                        fdr = L_i[j, 8] - d + 2048
                        if dlr < 0:
                            dlr = 0
                        if dlr > 255:
                            dlr = 255
                        if fdr < 0:
                            fdr = 0
                        if fdr > 4095:
                            fdr = 4095
                        ck[m] = (np.int64(L_i[j, 0]) << 40) | (np.int64(dlr) << 32) | (np.int64(fdr) << 20) | (np.int64(L_id[j]) & 0xFFFFF)
                        m += 1
                o = np.argsort(ck, kind='mergesort')
                req_v = 0.0
                alloc_v = 0.0
                forced_v = 0.0
                pend = 0
                i0 = 0
                while i0 < m3n:
                    s = L_i[cand[o[i0]], 0]
                    i1 = i0
                    while i1 < m3n and L_i[cand[o[i1]], 0] == s:
                        i1 += 1
                    P_ = pc[d, s]
                    av = adv20[d, s]
                    Bs = np.inf
                    if np.isfinite(av) and av > 0.0 and unit_cny > 0.0 and np.isfinite(pstar):
                        Bs = pstar * av / unit_cny
                    elif np.isfinite(pstar):
                        S_i[SI_FALLBACK] += 1
                        DY[d, DY_FALLBACK] += 1
                    base = regbuy[s] - sellfix[s]
                    fsum = 0.0
                    for ii in range(i0, i1):
                        j = cand[o[ii]]
                        if d + 1 >= L_i[j, 9]:
                            fsum += (L_f[j, 5] if gr else L_f[j, 0]) * P_
                    want_n = 0.0
                    for ii in range(i0, i1):
                        j = cand[o[ii]]
                        if not (d + 1 >= L_i[j, 9]):
                            want_n += (L_f[j, 5] if gr else L_f[j, 0]) * P_
                    bnet = base - fsum
                    if Bs == np.inf:
                        bud = want_n
                    else:
                        room_ = Bs + bnet
                        if room_ < 0.0:
                            room_ = 0.0
                        bud = want_n if want_n < room_ else room_
                    rem_want = want_n
                    for ii in range(i0, i1):
                        j = cand[o[ii]]
                        tgtq = L_f[j, 5] if gr else L_f[j, 0]   # E6r GATE_REARM：请求量 = 待关闭量（半量 / REARM 升级后的余量），不是整批
                        if not (P_ > 0.0):                     # 收盘价缺失：不造预算，回退原 NATIVE 全量请求（计数）
                            L_f[j, 4] = tgtq
                            S_i[SI_FALLBACK] += 1
                            continue
                        qv = tgtq * P_
                        req_v += qv
                        if d + 1 >= L_i[j, 9]:
                            L_f[j, 4] = tgtq
                            L_i[j, 13] = 1
                            forced_v += qv
                            alloc_v += qv
                            S_i[SI_OVERRIDE] += 1
                            DY[d, DY_M3OVR] += 1
                        else:
                            if bud >= rem_want * (1.0 - 1e-12):   # 余下预算覆盖其余全部请求 → 全量（逐项相减的舍入不造碎屑；p* → ∞ 与 NATIVE 恒等）
                                take = qv
                            else:
                                take = qv if qv < bud else bud
                            if take < 0.0:
                                take = 0.0
                            bud -= take
                            rem_want -= qv
                            L_f[j, 4] = take / P_ if P_ > 0.0 else 0.0
                            if take >= qv * (1.0 - 1e-12):
                                L_f[j, 4] = tgtq
                            alloc_v += take
                            if take < qv * (1.0 - 1e-12):
                                pend += 1
                    i0 = i1
                DY[d, DY_M3REQ] = req_v
                DY[d, DY_M3ALLOC] = alloc_v
                DY[d, DY_M3FORCED] = forced_v
                DY[d, DY_M3PEND] = pend
        # ---- E6q 新名字（T 收盘物理库存为零；本引擎买单当日计划次日执行，无跨日未完成买单）与常规买路由合格标志
        if m1 or route_on or rtm != RT_NONE:
            for k2 in range(a, b):
                s = f_col[k2]
                isnew[s] = not (q[s] > 1e-12)
        if route_on:
            for k in range(npb):
                s = PB_i[k, 0]
                ok_ = True
                if m1:
                    ok_ = isnew[s]
                if m2:
                    ok_ = ok_ and (regbuy[s] - sellfix[s] <= capx[s] * (1.0 + 1e-12) + 1e-9)
                PB_i[k, 2] = 1 if ok_ else 0
        # 额外批次计划（可用标签 K；先扣常规的预期缺口）
        extra_plan = 0.0
        if exit_on and fund == FD_NATIVE:
            K = 0.0
            for j in range(S_i[SI_NTK]):
                if TK_i[j, 2] == 1 and tk_ok(TK_i, j, d + 1, ttl):
                    if (not remain) or TK_i[j, 1] >= d + 2:
                        K += TK_f[j]
            short_res = 0.0
            if K > 1e-12:
                tag_all2 = tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, False, ttl)
                lk_all2 = tk_sum(LK_f, LK_i, S_i[SI_NLK], d + 1, False, 0)
                ordn = S_f[SF_CASH] - tag_all2 - lk_all2
                due_proc = 0.0
                for j in range(nl):
                    if L_i[j, 7] == 1 and L_f[j, 0] > 0.0 and (L_i[j, 3] == LQ_DUE or (L_i[j, 3] == LQ_NONE and L_i[j, 2] <= d + 1)):
                        due_proc += L_f[j, 0] * pc[d, L_i[j, 0]]
                regn = 0.0
                regn_el = 0.0
                for k in range(npb):
                    regn += PB_f[k]
                    if route_on and PB_i[k, 2] == 1:
                        regn_el += PB_f[k]
                short = regn - (ordn + due_proc)
                if short > 0.0:
                    if route_on:
                        short = short if short < regn_el else regn_el
                    K -= short
                    short_res = short
            if K > 1e-12 and (m1 or m2 or rtm != RT_NONE):
                npb, extra_plan = plan_e6q(d, K, a, b, f_col, f_w, expv, indsum, ind, capsh, idev, cap_s, NAVc, m1, m2, rtm, isnew, capx,
                                           regbuy, sellfix, seed, nodes, PB_i, PB_f, npb, TK_f, TK_i, S_i, ttl, short_res, DY, DBG)
            elif K > 1e-12:
                if rmode == RY_COST0 or rmode == RY_COSTNET:
                    npb, extra_plan = plan_routed(d, K, a, b, f_col, f_w, nl, L_i, L_f, pc, expv, indsum, ind, capsh, idev, cap_s, NAVc, V0,
                                                  sig20, adv20, rA, rK, rD, p0, c, rmode, PB_i, PB_f, npb, sellv, DY)
                elif ovl != OV_NONE:
                    # E6r：额外批次同过入场算子——先按 E6q 原式（顺序截断、行业余量逐名扣减）在临时累加上算 x⁰，再按同一算子改票据，最后提交（不重复乘 λ）
                    p0x = npb
                    for g in range(G):
                        ov_indtmp[g] = indsum[g]
                    for k2 in range(a, b):
                        s = f_col[k2]
                        x = K * f_w[k2]
                        if not (x > 0.0):
                            continue
                        room = cap_s - expv[s]
                        g = ind[d, s]
                        if g >= 0:
                            room = min(room, (capsh[d, g] + idev) * NAVc - ov_indtmp[g])
                        if room <= 0.0:
                            continue
                        x = min(x, room)
                        PB_i[npb, 0] = s
                        PB_i[npb, 1] = 1
                        PB_i[npb, 2] = -1
                        PB_i[npb, 3] = k2
                        PB_f[npb] = x
                        pb_x0[npb] = x
                        if g >= 0:
                            ov_indtmp[g] += x
                        npb += 1
                    crho_on = crho and b > a
                    ov_apply(d, p0x, npb, PB_i, PB_f, a, ov_rho, ov_lab, ov_st, ov_cell, ov_pin, seckey, expv, indsum, ind, capsh, idev, scap, NAVc,
                             ovl, ernd, seed, nodes, rtv, S_i, DY, True, pb_lab, crho_on, rho_c, lab_c, keep_c)
                    for k in range(p0x, npb):
                        s = PB_i[k, 0]
                        k2 = PB_i[k, 3]
                        x = PB_f[k]
                        expv[s] += x
                        g = ind[d, s]
                        if g >= 0:
                            indsum[g] += x
                        extra_plan += x
                        if PL_i[s, 5] == 0:
                            lb = pb_lab[k]
                            PL_i[s, 0] = d
                            PL_i[s, 1] = lb
                            PL_i[s, 2] = ov_lab20[k2]
                            PL_i[s, 3] = ov_st[k2]
                            PL_i[s, 4] = (30 if lb == 1 else (20 if lb == 2 else (10 if lb == 3 else H))) if ovl == OV_TILTH else H
                            PL_i[s, 5] = 1
                            PL_f[s, 0] = f_w[k2]
                            PL_f[s, 1] = f_w[k2] * ov_rho[k2]
                            PL_f[s, 2] = 0.0
                            PL_f[s, 3] = 0.0
                        PL_f[s, 4] = x
                        PL_f[s, 5] = pb_x0[k]
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
                        PB_i[npb, 3] = k2
                        PB_f[npb] = x
                        expv[s] += x
                        if g >= 0:
                            indsum[g] += x
                        extra_plan += x
                        npb += 1
                        if PL_i[s, 5] == 0:
                            PL_i[s, 0] = d
                            PL_i[s, 1] = ov_lab[k2]
                            PL_i[s, 2] = ov_lab20[k2]
                            PL_i[s, 3] = ov_st[k2]
                            PL_i[s, 4] = H
                            PL_i[s, 5] = 1
                            PL_f[s, 0] = f_w[k2]
                            PL_f[s, 1] = f_w[k2]
                            PL_f[s, 2] = 0.0
                            PL_f[s, 3] = 0.0
                        PL_f[s, 4] = x
                        PL_f[s, 5] = x
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
                ordn2 = S_f[SF_CASH] - tk_sum(TK_f, TK_i, S_i[SI_NTK], d + 1, False, ttl) - tk_sum(LK_f, LK_i, S_i[SI_NLK], d + 1, False, 0)
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
def select_bern(d, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, p_bern, sec_new_int, sec_due_max, mk_i, mk_f, fhit):
    """BERNOULLI：逐批概率 = owner 同 H 无退出父影子风险集前 60 日风险率（p_bern[d, 日龄层]，历史不足 NaN = 不抽）。
    E6q FIRSTHIT（fhit）：每批一次事件（抽中即记 L_i[12]，未成交也不重抽）；M4 已开 episode 的余半不入风险集。"""
    nl = S_i[SI_NL]
    nsel = 0
    for j in range(nl):
        if L_i[j, 7] != 1 or L_i[j, 3] != LQ_NONE or L_i[j, 1] > d or not (d + 1 < L_i[j, 2]):
            continue
        if L_i.shape[1] > 12 and (L_i[j, 10] != 0 or (fhit and L_i[j, 12] == 1)):
            continue
        lay = min(d - L_i[j, 1], NL - 1)
        p = p_bern[d, lay]
        if np.isfinite(p) and p > 0.0 and hash_u(seed, d, L_id[j]) < p:
            if fhit and L_i.shape[1] > 12:
                L_i[j, 12] = 1
            nsel += mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, lay, sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, KD_RAND,
                               mk_i, mk_f)
    return nsel


@njit(cache=True)
def take_amount(d, j, tgt, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, sec_new_int, sec_due_max, kind, mk_i, mk_f):
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
        if L_i.shape[1] > 17:                        # E6r：拆出的批次继承形成标签（cohort / 标签 / 状态）
            for cc in range(14, 18):
                L_i[nj, cc] = L_i[j, cc]
        L_f[j, 0] -= L_f[nj, 0]
        if L_f.shape[1] > 4:
            L_f[j, 4] = L_f[j, 0]
        mark_early(d, nj, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[nj, 1], NL - 1), sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind,
                   mk_i, mk_f)
        return tgt, False
    mark_early(d, j, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, min(d - L_i[j, 1], NL - 1), sec_new_int, sec_due_max, t1a, lvl, recon, u_ptr, u_col, kind,
               mk_i, mk_f)
    return v, True


@njit(cache=True)
def select_v2(d, smode, seed, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, cpct, iskid, t1a, lvl, recon, u_ptr, u_col,
              tg_b, tg_isk2, tg_aisk, sec_new_int, sec_due_max, DY, mk_i, mk_f):
    """V2 随机 / 水平控制（plan §8.1；只用本路径 T 收盘库存与 owner T 收盘意向目标）：
    AMT2 / LVL2：日龄桶内同金额 → 本路径全部 R_INTENT 回填（LVL2 = 当日日 CVR 位置降序，确定性）；AISK2：行业 × size × 日龄桶内同金额 → 全域回填；
    ISK2：行业 × size × 日龄桶同唯一证券数 → 行业 × 日龄 → 日龄 依次回填（证券全部可干预批次一起）。每日记 requested / within / cross / unmatched。"""
    nl = S_i[SI_NL]
    cnt = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0 and L_i[j, 10] == 0:
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
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0 and L_i[j, 10] == 0:
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
                                             sec_new_int, sec_due_max, KD_RAND, mk_i, mk_f)
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
                                             sec_new_int, sec_due_max, KD_RAND, mk_i, mk_f)
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
                                             sec_new_int, sec_due_max, KD_RAND, mk_i, mk_f)
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
                                             sec_new_int, sec_due_max, KD_RAND, mk_i, mk_f)
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
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND, mk_i, mk_f)
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
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND, mk_i, mk_f)
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
                                           t1a, lvl, recon, u_ptr, u_col, KD_RAND, mk_i, mk_f)
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
def select_rchk(d, seed, NL, renew, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, tgt, sec_new_int, sec_due_max, DY, mk_i, mk_f):
    """R_CHECKPOINT：只在同五日检查点批次内、按稳定哈希序取消与 owner 同金额的持有许可（末批可部分）；非检查点不随机退出。"""
    nl = S_i[SI_NL]
    cnt = 0
    for j in range(nl):
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0 and L_i[j, 10] == 0:
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
        if L_i[j, 7] == 1 and L_i[j, 3] == LQ_NONE and L_i[j, 1] <= d and d + 1 < L_i[j, 2] and L_f[j, 0] > 0.0 and L_i[j, 10] == 0:
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
        got, whole = take_amount(d, j, left, NL, L_i, L_f, L_id, IN_i, IN_f, S_i, pc, iskid, t1a, lvl, recon, u_ptr, u_col, sec_new_int, sec_due_max, KD_RCHK, mk_i, mk_f)
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


@njit(cache=True)
def rt_fits(t, room):
    """票据 t 能否放进余量 room（相对容差 1e−9：引擎单位为 1 亿量级，绝对 1e−10 低于浮点分辨率，会把本臂自身的可行分配误判为不可行）。"""
    return t <= room + 1e-9 * max(1.0, t)


@njit(cache=True)
def rt_feasible_rest(i, tickets, cap, grp, grem, used, er, gcap):
    """剪枝的必要条件（只删除无可行补全的子树，因此找到的仍是不剪枝 DFS 序下的首个可行解，PROVED_NO_MATCH 仍是穷尽证明）。
    记未用候选的有效余量 r_c = min(单股余量, 所属行业余量)，余下票据降序 t_1 ≥ t_2 ≥ …：
    ① 名额：对每个 k，r_c ≥ t_k 的未用候选至少 k 个（每票须占一个不同证券，且该证券能容下它）；
    ② 阈值嵌套的金额容量：对每个 k，前 k 大票据总额 ≤ Σ_行业 min(行业余量, 该行业中 r_c ≥ t_k 的未用候选单股余量和) + 无行业此类候选余量和
       （前 k 大票据每张都 ≥ t_k，只能放进 r_c ≥ t_k 的候选，且同一行业合计不超过行业余量）。"""
    nt = len(tickets)
    nc = len(cap)
    rem_n = nt - i
    m = 0
    for c in range(nc):
        if used[c]:
            continue
        g = grp[c]
        r = cap[c]
        if g >= 0 and grem[g] < r:
            r = grem[g]
        if r > 0.0:
            er[m] = r
            m += 1
    if rem_n > m:
        return False
    ec = np.empty(m, np.int64)
    m2 = 0
    for c in range(nc):
        if used[c]:
            continue
        g = grp[c]
        r = cap[c]
        if g >= 0 and grem[g] < r:
            r = grem[g]
        if r > 0.0:
            ec[m2] = c
            m2 += 1
    o = np.argsort(-er[:m], kind='mergesort')
    for k in range(rem_n):
        if not rt_fits(tickets[i + k], er[o[k]]):
            return False
    G = len(grem)
    for g in range(G):
        gcap[g] = 0.0
    tot = 0.0
    cum = 0.0
    p = 0
    for k in range(rem_n):
        tau = tickets[i + k]
        cum += tau
        while p < m and rt_fits(tau, er[o[p]]):
            c = ec[o[p]]
            g = grp[c]
            if g >= 0:
                old = gcap[g] if gcap[g] < grem[g] else grem[g]
                gcap[g] += cap[c]
                new = gcap[g] if gcap[g] < grem[g] else grem[g]
                tot += new - old
            else:
                tot += cap[c]
            p += 1
        if not rt_fits(cum, tot):
            return False
    # ③ 行业最低吸收额：其余候选 O_g 最多能吸收的票据总额 W*（嵌套相容 → 拟阵贪心：票据降序，第 c+1 张须 ≤ O_g 第 c+1 大有效余量），
    #    余下总额 − W* 是行业 g 至少要吸收的额度，须 ≤ g 的行业余量
    total = 0.0
    for k in range(i, nt):
        total += tickets[k]
    for g in range(G):
        if not (grem[g] > 0.0):
            continue
        has = False
        for q in range(m):
            if grp[ec[o[q]]] == g:
                has = True
                break
        if not has:
            continue
        wsum = 0.0
        q0 = 0
        for k in range(i, nt):
            q = q0
            while q < m and grp[ec[o[q]]] == g:
                q += 1
            if q >= m:
                break
            if rt_fits(tickets[k], er[o[q]]):
                wsum += tickets[k]
                q0 = q + 1
        if total - wsum > grem[g] + 1e-9 * max(1.0, total):
            return False
    # ④ 余下票据中重数最大的同额类须能按行业计数放下（rt_bulk_ok 精确；忽略其余票据 → 必要条件）
    bv = tickets[i]
    bn = 0
    k = i
    while k < nt:
        v = tickets[k]
        cc = 0
        while k < nt and tickets[k] == v:
            cc += 1
            k += 1
        if cc > bn:
            bn = cc
            bv = v
    if bn > 1 and not rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
        return False
    return True


@njit(cache=True)
def rt_kfloor(rem, v):
    """行业余量 rem 最多能放几张金额 v 的票据（与 rt_fits 同容差的逐张放置等价：k·v ≤ rem + 1e−9·max(1, v)）。"""
    if not (rem > 0.0):
        return 0
    return int(np.floor((rem + 1e-9 * max(1.0, v)) / v))


@njit(cache=True)
def rt_bulk_ok(vb, nb, cap, grp, grem, used, G):
    """nb 张同额 vb 票据能否全部放下（精确）：每行业最多 min(未用且单股余量 ≥ vb 的候选数, ⌊行业余量 / vb⌋) 张，无行业候选各 1 张。"""
    if nb <= 0:
        return True
    cnt = np.zeros(G + 1, np.int64)
    for c in range(len(cap)):
        if used[c] or not rt_fits(vb, cap[c]):
            continue
        g = grp[c]
        if g >= 0:
            cnt[g] += 1
        else:
            cnt[G] += 1
    tot = cnt[G]
    for g in range(G):
        if cnt[g] > 0:
            k = rt_kfloor(grem[g], vb)
            tot += cnt[g] if cnt[g] < k else k
            if tot >= nb:
                return True
    return tot >= nb


@njit(cache=True)
def rt_oracle(i0, tickets, cap, grp, grem, used, budget, eorder):
    """精确可行性判定：剩余票据 tickets[i0:]（降序）能否全部放下。把剩余票据中重数最大的同额类作"大类"（只计数，rt_bulk_ok 精确），
    对其余票据按金额降序、候选按有效余量升序（best-fit）回溯，同额小票据用对称性；每个节点先核大类计数（必要条件，放小票据只会减少容量）。
    不改动 used / grem（返回前全部撤销）。返回 (1 可行 / 0 不可行 / −1 节点超限, 节点数)。"""
    nt = len(tickets)
    nc = len(cap)
    G = len(grem)
    if i0 >= nt:
        return 1, 0
    bv = tickets[i0]
    bn = 0
    k = i0
    while k < nt:
        v = tickets[k]
        c = 0
        while k < nt and tickets[k] == v:
            c += 1
            k += 1
        if c > bn:
            bn = c
            bv = v
    ns = (nt - i0) - bn
    small = np.empty(max(ns, 1), np.int64)
    m = 0
    for k in range(i0, nt):
        if tickets[k] != bv:
            small[m] = k
            m += 1
    if not rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
        return 0, 1
    if ns == 0:
        return 1, 1
    assign = np.full(ns, -1, np.int64)
    pos = np.zeros(ns + 1, np.int64)
    fresh = np.ones(ns + 1, np.bool_)
    j = 0
    nodes = 1
    res = 0
    while True:
        if j == ns:
            if rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
                res = 1
                break
            j -= 1
            ci = assign[j]
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[j]]
            assign[j] = -1
            continue
        found = False
        if fresh[j]:
            fresh[j] = False
            pos[j] = pos[j - 1] if (j > 0 and tickets[small[j]] == tickets[small[j - 1]]) else 0
            nodes += 1
            if nodes > budget:
                res = -1
                break
            if not rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
                pos[j] = nc
        while pos[j] < nc:
            ci = eorder[pos[j]]
            pos[j] += 1
            nodes += 1
            if nodes > budget:
                break
            if used[ci]:
                continue
            t = tickets[small[j]]
            if not rt_fits(t, cap[ci]):
                continue
            g = grp[ci]
            if g >= 0 and not rt_fits(t, grem[g]):
                continue
            used[ci] = True
            assign[j] = ci
            if g >= 0:
                grem[g] -= t
            found = True
            break
        if nodes > budget:
            res = -1
            break
        if found:
            j += 1
            fresh[j] = True
        else:
            fresh[j] = True
            j -= 1
            if j < 0:
                res = 0
                break
            ci = assign[j]
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[j]]
            assign[j] = -1
    for jj in range(ns):
        ci = assign[jj]
        if ci >= 0:
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[jj]]
    return res, nodes


@njit(cache=True)
def rt_match_oracle(tickets, cap, grp, grem, order, limit):
    """（备选实现，未用于生产；见 notes）RANDOM_TARGET 精确首个可行匹配。
    实现 = 字典序贪心 + 精确可行性判定（rt_oracle）：逐张票据按优先序试候选，只在"剩余票据仍可全部放下"时落定——与不剪枝 DFS 的首个解相同；
    同额票据按优先序递增（同额互换 = 同一实际分配）。初始判定不可行 → PROVED_NO_MATCH；任一判定超节点上限 → ALGORITHM_LIMIT（不换种子）。
    返回 (assign[票] = 候选序号或 −1, 状态, 节点数)；grem 原地使用（调用方传副本）。"""
    nt = len(tickets)
    nc = len(cap)
    assign = np.full(nt, -1, np.int64)
    used = np.zeros(nc, np.bool_)
    er = np.empty(max(nc, 1))
    for c in range(nc):
        g = grp[c]
        r = cap[c]
        if g >= 0 and grem[g] < r:
            r = grem[g]
        er[c] = r
    eorder = np.argsort(er, kind='mergesort')
    lim = limit if limit > 0 else 1 << 62
    st, nodes = rt_oracle(0, tickets, cap, grp, grem, used, lim, eorder)
    if st == 0:
        return assign, RTS_NOMATCH, nodes
    if st < 0:
        return assign, RTS_LIMIT, nodes
    ppos = np.zeros(nt + 1, np.int64)
    for i in range(nt):
        start = ppos[i - 1] + 1 if (i > 0 and tickets[i] == tickets[i - 1]) else 0
        placed = False
        t = tickets[i]
        for p in range(start, nc):
            ci = order[p]
            nodes += 1
            if used[ci] or not rt_fits(t, cap[ci]):
                continue
            g = grp[ci]
            if g >= 0 and not rt_fits(t, grem[g]):
                continue
            used[ci] = True
            if g >= 0:
                grem[g] -= t
            st, nn = rt_oracle(i + 1, tickets, cap, grp, grem, used, lim - nodes, eorder)
            nodes += nn
            if st == 1:
                assign[i] = ci
                ppos[i] = p
                placed = True
                break
            used[ci] = False
            if g >= 0:
                grem[g] += t
            if st < 0 or nodes > lim:
                for k in range(nt):
                    assign[k] = -1
                return assign, RTS_LIMIT, nodes
        if not placed:
            for k in range(nt):
                assign[k] = -1
            return assign, RTS_LIMIT, nodes
    return assign, RTS_FEASIBLE, nodes


@njit(cache=True)
def rt_match(tickets, cap, grp, grem, order, limit):
    """RANDOM_TARGET 精确首个可行匹配（plan 附录 C match_tickets 同语义）：票据按金额降序（已排好），逐票按固定优先序找第一个
    未用、≤ 单股余量、≤ 行业余量的证券，失败则确定性回溯；每层入口先做必要条件剪枝（rt_feasible_rest，不改变首个可行解）；
    节点数达 limit → ALGORITHM_LIMIT（不换种子）；穷尽 → PROVED_NO_MATCH。返回 (assign[票] = 候选序号或 −1, 状态, 节点数)；grem 原地使用（调用方传副本）。"""
    nt = len(tickets)
    nc = len(cap)
    assign = np.full(nt, -1, np.int64)
    used = np.zeros(nc, np.bool_)
    pos = np.zeros(nt + 1, np.int64)
    fresh = np.ones(nt + 1, np.bool_)
    er = np.empty(max(nc, 1))
    gcap = np.empty(max(len(grem), 1))
    i = 0
    nodes = 0
    status = RTS_FEASIBLE
    while i < nt:
        found = False
        if fresh[i]:
            fresh[i] = False
            # 对称性：与上一张票据金额完全相同（逐位相等）时，只在上一张所占候选之后的优先位置找（同额票据互换 = 同一实际分配，
            # 其另一排列已在先前分支被穷尽，跳过它不改变首个可行解；见 notes：RANDOM_TARGET 求解器）
            pos[i] = pos[i - 1] if (i > 0 and tickets[i] == tickets[i - 1]) else 0
            nodes += 1
            if limit > 0 and nodes > limit:
                return assign, RTS_LIMIT, nodes
            if not rt_feasible_rest(i, tickets, cap, grp, grem, used, er, gcap):
                pos[i] = nc
        while pos[i] < nc:
            ci = order[pos[i]]
            pos[i] += 1
            nodes += 1
            if limit > 0 and nodes > limit:
                return assign, RTS_LIMIT, nodes
            if used[ci]:
                continue
            t = tickets[i]
            if not rt_fits(t, cap[ci]):
                continue
            g = grp[ci]
            if g >= 0 and not rt_fits(t, grem[g]):
                continue
            used[ci] = True
            assign[i] = ci
            if g >= 0:
                grem[g] -= t
            found = True
            break
        if found:
            i += 1
            fresh[i] = True
        else:
            fresh[i] = True
            i -= 1
            if i < 0:
                status = RTS_NOMATCH
                break
            ci = assign[i]
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[i]
            assign[i] = -1
    if status == RTS_NOMATCH:
        for k in range(nt):
            assign[k] = -1
    return assign, status, nodes


@njit(cache=True)
def rt_eorder(cap, grp, grem):
    """候选按有效余量 min(单股余量, 行业余量) 升序（best-fit 序；并列按候选序号）。"""
    nc = len(cap)
    er = np.empty(max(nc, 1))
    for c in range(nc):
        g = grp[c]
        r = cap[c]
        if g >= 0 and grem[g] < r:
            r = grem[g]
        er[c] = r
    return np.argsort(er[:nc], kind='mergesort')


@njit(cache=True)
def rt_complete_bfd(i0, tickets, cap, grp, grem, used, out):
    """BFD 补全（可行补全的充分证书）：票据 tickets[i0:]（降序）逐张放进未用、单股与行业余量都容得下的候选中有效余量最小者
    （并列取候选序号小者）；全部放下 → True、out[i0:] = 候选。只读 used / grem（内部副本）。"""
    nt = len(tickets)
    nc = len(cap)
    u2 = used.copy()
    g2 = grem.copy()
    for k in range(i0, nt):
        t = tickets[k]
        best = -1
        bestr = 0.0
        for c in range(nc):
            if u2[c] or not rt_fits(t, cap[c]):
                continue
            g = grp[c]
            r = cap[c]
            if g >= 0:
                if not rt_fits(t, g2[g]):
                    continue
                if g2[g] < r:
                    r = g2[g]
            if best < 0 or r < bestr:
                best = c
                bestr = r
        if best < 0:
            return False
        out[k] = best
        u2[best] = True
        g = grp[best]
        if g >= 0:
            g2[g] -= t
    return True


@njit(cache=True)
def rt_oracle2(i0, tickets, cap, grp, grem, used, budget, eorder, out):
    """rt_oracle 同判定（剩余票据中重数最大的同额类只计数、其余 best-fit 序回溯、同额对称性），另在可行时把一个完整补全写进 out[i0:]
    （小票据 = 回溯所得；大类按候选序号逐个放，每行业放到 min(容得下的未用候选数, ⌊行业余量 / 额⌋) = rt_bulk_ok 的计数）。
    不改动 used / grem（返回前全部撤销）。返回 (1 可行 / 0 不可行 / −1 节点超限, 节点数)。"""
    nt = len(tickets)
    nc = len(cap)
    G = len(grem)
    if i0 >= nt:
        return 1, 0
    bv = tickets[i0]
    bn = 0
    k = i0
    while k < nt:
        v = tickets[k]
        c = 0
        while k < nt and tickets[k] == v:
            c += 1
            k += 1
        if c > bn:
            bn = c
            bv = v
    ns = (nt - i0) - bn
    small = np.empty(max(ns, 1), np.int64)
    m = 0
    for k in range(i0, nt):
        if tickets[k] != bv:
            small[m] = k
            m += 1
    if not rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
        return 0, 1
    assign = np.full(max(ns, 1), -1, np.int64)
    pos = np.zeros(ns + 1, np.int64)
    fresh = np.ones(ns + 1, np.bool_)
    j = 0
    nodes = 1
    res = 0
    while True:
        if j == ns:
            if rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
                res = 1
                break
            if ns == 0:
                res = 0
                break
            j -= 1
            ci = assign[j]
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[j]]
            assign[j] = -1
            continue
        found = False
        if fresh[j]:
            fresh[j] = False
            pos[j] = pos[j - 1] if (j > 0 and tickets[small[j]] == tickets[small[j - 1]]) else 0
            nodes += 1
            if nodes > budget:
                res = -1
                break
            if not rt_bulk_ok(bv, bn, cap, grp, grem, used, G):
                pos[j] = nc
        while pos[j] < nc:
            ci = eorder[pos[j]]
            pos[j] += 1
            nodes += 1
            if nodes > budget:
                break
            if used[ci]:
                continue
            t = tickets[small[j]]
            if not rt_fits(t, cap[ci]):
                continue
            g = grp[ci]
            if g >= 0 and not rt_fits(t, grem[g]):
                continue
            used[ci] = True
            assign[j] = ci
            if g >= 0:
                grem[g] -= t
            found = True
            break
        if nodes > budget:
            res = -1
            break
        if found:
            j += 1
            fresh[j] = True
        else:
            fresh[j] = True
            j -= 1
            if j < 0:
                res = 0
                break
            ci = assign[j]
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[j]]
            assign[j] = -1
    if res == 1:
        for jj in range(ns):
            out[small[jj]] = assign[jj]
        u2 = used.copy()
        g2 = grem.copy()
        kk = i0
        placed = 0
        for c in range(nc):
            while kk < nt and tickets[kk] != bv:
                kk += 1
            if kk >= nt:
                break
            if u2[c] or not rt_fits(bv, cap[c]):
                continue
            g = grp[c]
            if g >= 0:
                if not rt_fits(bv, g2[g]):
                    continue
                g2[g] -= bv
            u2[c] = True
            out[kk] = c
            kk += 1
            placed += 1
        if placed != bn:
            res = -1                                   # 防御（rt_bulk_ok 计数保证放得下）：按触限处理，不当可行
    for jj in range(ns):
        ci = assign[jj]
        if ci >= 0:
            used[ci] = False
            g = grp[ci]
            if g >= 0:
                grem[g] += tickets[small[jj]]
    return res, nodes


@njit(cache=True)
def rt_match2(tickets, cap, grp, grem, order, limit, wit, S_i):
    """E6R_TICKETS_LEXGREEDY_WITNESS_V2：与 rt_match 同语义——票据降序，逐票按固定优先序取第一个"存在可行补全"的候选（= 不剪枝 DFS 的首个可行解；
    同额票据只在上一张所占位置之后找，同 rt_match）；实现 = 字典序贪心 + 可行补全判定，依次：① 见证 W（完整可行分配，初值 = 原映射 wit）
    已把票据 i 放在该候选 → 成立；② 2-交换（该候选在 W 中的票据换到 W[i]）满足单股余量与两行业合计 → 成立；③ BFD 补全成功 → 成立；
    ④ 必要条件（rt_feasible_rest）不过 → 不成立；⑤ 精确回溯（rt_oracle2）在剩余节点预算内判定，预算用尽 → ALGORITHM_LIMIT（整次）。
    节点 = 候选检查数 + 精确回溯节点；上限同 rt_match（limit）。wit 不合法（非双射 / 超余量）→ 先用 BFD / 精确回溯求初始 W，不可行 → PROVED_NO_MATCH。
    返回 (assign[票] = 候选序号或 −1, 状态, 节点数)；grem 原地使用（调用方传副本）。"""
    nt = len(tickets)
    nc = len(cap)
    G = len(grem)
    assign = np.full(nt, -1, np.int64)
    used = np.zeros(nc, np.bool_)
    W = np.full(nt, -1, np.int64)
    holder = np.full(nc, -1, np.int64)
    gW = np.zeros(max(G, 1))
    tmp = np.full(nt, -1, np.int64)
    er = np.empty(max(nc, 1))
    gcb = np.empty(max(G, 1))
    g0 = grem.copy()
    nodes = 0
    lim = limit if limit > 0 else (1 << 62)
    ok = nt <= nc and len(wit) == nt
    if ok:
        for k in range(nt):
            c = wit[k]
            if c < 0 or c >= nc or holder[c] >= 0 or not rt_fits(tickets[k], cap[c]):
                ok = False
                break
            holder[c] = k
            g = grp[c]
            if g >= 0:
                gW[g] += tickets[k]
        if ok:
            for g in range(G):
                if gW[g] > 0.0 and not rt_fits(gW[g], g0[g]):
                    ok = False
                    break
    if ok:
        for k in range(nt):
            W[k] = wit[k]
    else:
        for c in range(nc):
            holder[c] = -1
        for g in range(G):
            gW[g] = 0.0
        if rt_complete_bfd(0, tickets, cap, grp, grem, used, tmp):
            S_i[SI_RTBFD] += 1
        else:
            nodes += 1
            if not rt_feasible_rest(0, tickets, cap, grp, grem, used, er, gcb):
                return assign, RTS_NOMATCH, nodes
            eo = rt_eorder(cap, grp, grem)
            st, nn = rt_oracle2(0, tickets, cap, grp, grem, used, lim - nodes, eo, tmp)
            nodes += nn
            S_i[SI_RTEXACT] += 1
            if st == 0:
                return assign, RTS_NOMATCH, nodes
            if st < 0:
                return assign, RTS_LIMIT, nodes
        for k in range(nt):
            W[k] = tmp[k]
            holder[W[k]] = k
            g = grp[W[k]]
            if g >= 0:
                gW[g] += tickets[k]
    ppos = np.zeros(nt, np.int64)
    for i in range(nt):
        t = tickets[i]
        start = ppos[i - 1] + 1 if (i > 0 and tickets[i] == tickets[i - 1]) else 0
        placed = False
        for p in range(start, nc):
            c = order[p]
            nodes += 1
            if nodes > lim:
                return assign, RTS_LIMIT, nodes
            if used[c] or not rt_fits(t, cap[c]):
                continue
            g = grp[c]
            if g >= 0 and not rt_fits(t, grem[g]):
                continue
            fe = W[i] == c
            if not fe:
                j = holder[c]
                ci = W[i]
                ga = grp[c]
                gb = grp[ci]
                tj = tickets[j] if j >= 0 else 0.0
                if j < 0 or rt_fits(tj, cap[ci]):
                    okg = True
                    if ga != gb:
                        if ga >= 0 and t > tj and not rt_fits(gW[ga] + t - tj, g0[ga]):
                            okg = False
                        if gb >= 0 and tj > t and not rt_fits(gW[gb] + tj - t, g0[gb]):
                            okg = False
                    if okg:
                        W[i] = c
                        holder[c] = i
                        holder[ci] = j
                        if j >= 0:
                            W[j] = ci
                        if ga != gb:
                            if ga >= 0:
                                gW[ga] += t - tj
                            if gb >= 0:
                                gW[gb] += tj - t
                        fe = True
                        S_i[SI_RTSWAP] += 1
                if not fe:
                    used[c] = True
                    if g >= 0:
                        grem[g] -= t
                    lim_hit = False
                    if rt_complete_bfd(i + 1, tickets, cap, grp, grem, used, tmp):
                        fe = True
                        S_i[SI_RTBFD] += 1
                    else:
                        nodes += 1
                        if rt_feasible_rest(i + 1, tickets, cap, grp, grem, used, er, gcb):
                            eo = rt_eorder(cap, grp, grem)
                            st, nn = rt_oracle2(i + 1, tickets, cap, grp, grem, used, lim - nodes, eo, tmp)
                            nodes += nn
                            S_i[SI_RTEXACT] += 1
                            if st < 0:
                                lim_hit = True
                            fe = st == 1
                    used[c] = False
                    if g >= 0:
                        grem[g] += t
                    if lim_hit:
                        return assign, RTS_LIMIT, nodes
                    if fe:
                        for k in range(nc):
                            holder[k] = -1
                        for gg in range(G):
                            gW[gg] = 0.0
                        for k in range(nt):
                            if k < i:
                                W[k] = assign[k]
                            elif k == i:
                                W[k] = c
                            else:
                                W[k] = tmp[k]
                            holder[W[k]] = k
                            gg = grp[W[k]]
                            if gg >= 0:
                                gW[gg] += tickets[k]
            if fe:
                assign[i] = c
                used[c] = True
                if g >= 0:
                    grem[g] -= t
                ppos[i] = p
                placed = True
                break
        if not placed:
            return assign, RTS_LIMIT, nodes                  # 见证保证不发生（W[i] 位于 start 之后且可行）；防御：按触限记
    return assign, RTS_FEASIBLE, nodes


@njit(cache=True)
def rt_dispatch(tick, ccap, cg, g2, o, nodes, rtv, wit, S_i):
    """入场 TICKETS / JOINT 求解器分派：rtv 0 = rt_match（v1 回溯）；1 = rt_match2（v2，生产）；2 = 两版同跑逐实例比对（结果用 v2；
    v1 可行时 v2 须逐位同解，否则记 SI_RTMIS；v1 触限、v2 求得首解记 SI_RTV1OK）。"""
    if rtv == 0:
        return rt_match(tick, ccap, cg, g2, o, nodes)
    if rtv == 2:
        a1, s1, n1 = rt_match(tick, ccap, cg, g2.copy(), o, nodes)
        a2, s2, n2 = rt_match2(tick, ccap, cg, g2, o, nodes, wit, S_i)
        S_i[SI_RTCMP] += 1
        S_i[SI_RTN1] += n1
        S_i[SI_RTN2] += n2
        if s1 == RTS_FEASIBLE:
            same = s2 == RTS_FEASIBLE
            if same:
                for k in range(len(a1)):
                    if a1[k] != a2[k]:
                        same = False
                        break
            if not same:
                S_i[SI_RTMIS] += 1
        elif s1 == RTS_LIMIT:
            S_i[SI_RTV1LIM] += 1
            if s2 == RTS_FEASIBLE:
                S_i[SI_RTV1OK] += 1
        else:
            if s2 != s1:
                S_i[SI_RTMIS] += 1
        if s2 == RTS_LIMIT:
            S_i[SI_RTV2LIM] += 1
        return a2, s2, n2
    a2, s2, n2 = rt_match2(tick, ccap, cg, g2, o, nodes, wit, S_i)
    if s2 == RTS_LIMIT:
        S_i[SI_RTV2LIM] += 1
    return a2, s2, n2


@njit(cache=True)
def plan_e6q(d, K, a, b, f_col, f_w, expv, indsum, ind, capsh, idev, cap_s, NAVc, m1, m2, rtm, isnew, capx, regbuy, sellfix,
             seed, nodes, PB_i, PB_f, npb, TK_f, TK_i, S_i, ttl, short_res, DY, DBG):
    """E6q 额外批次计划（M1 / M2 / RANDOM_TARGET；plan §5.2 / §5.3 / §8.3）：
    ① NATIVE 同日可用额 native_use（E6p 原式顺序模拟：K·f_w 截到单股 / 行业余量）；
    ② 本臂票据：M1 在新名字内按 f_w 重归一；M2 再截到 max(0, B_s − b_s)；NATIVE 臂（只做随机目标）= 原式；
    ③ M1 / M2 拒绝额 = native_use − 本臂用量 > 0 → 消费序对应标签 first_denied = d + 1（已有不改）；
    ④ RANDOM_TARGET：同票据在本臂合法集（WITHIN）/ 源 cohort（SOURCE；M1 不再限新名字）内按五日块固定哈希优先序精确首个可行匹配；
       全用且等额 → IDENTITY；无解 / 节点上限 → 一次带上限部分分配并记短配。返回 (npb, extra_plan)。"""
    G = indsum.shape[0]
    ind_tmp = indsum.copy()
    native_use = 0.0
    nlist = 0
    for k2 in range(a, b):
        s = f_col[k2]
        x = K * f_w[k2]
        if not (x > 0.0):
            continue
        nlist += 1
        room = cap_s - expv[s]
        g = ind[d, s]
        if g >= 0:
            room = min(room, (capsh[d, g] + idev) * NAVc - ind_tmp[g])
        if room <= 0.0:
            continue
        x = min(x, room)
        native_use += x
        if g >= 0:
            ind_tmp[g] += x
    W_new = 0.0
    n_new = 0
    for k2 in range(a, b):
        if f_w[k2] > 0.0 and isnew[f_col[k2]]:
            W_new += f_w[k2]
            n_new += 1
    DY[d, DY_NEWN] = n_new
    DY[d, DY_LISTN] = nlist
    DY[d, DY_XNAT] = native_use
    n = b - a
    tk_s = np.empty(max(n, 1), np.int64)
    tk_x = np.empty(max(n, 1))
    nt = 0
    for g in range(G):
        ind_tmp[g] = indsum[g]
    arm_use = 0.0
    for k2 in range(a, b):
        s = f_col[k2]
        w = f_w[k2]
        if not (w > 0.0):
            continue
        if m1:
            if not isnew[s] or not (W_new > 0.0):
                continue
            x = K * w / W_new
        else:
            x = K * w
        room = cap_s - expv[s]
        g = ind[d, s]
        if g >= 0:
            room = min(room, (capsh[d, g] + idev) * NAVc - ind_tmp[g])
        if m2:
            cr = capx[s] - (regbuy[s] - sellfix[s])
            if cr < 0.0:
                cr = 0.0
            room = min(room, cr)
        if room <= 0.0:
            continue
        x = min(x, room)
        if not (x > 1e-15):
            continue
        tk_s[nt] = s
        tk_x[nt] = x
        nt += 1
        arm_use += x
        if g >= 0:
            ind_tmp[g] += x
    if m1 or m2:
        deny = native_use - arm_use
        if deny > 1e-12 * max(1.0, native_use):
            newm = tk_deny(TK_f, TK_i, S_i[SI_NTK], d + 1, short_res + arm_use, deny, ttl, d + 1)
            S_i[SI_DENY] += newm
            DY[d, DY_DENY] = deny
            DY[d, DY_DENYN] = newm
        if m1 and n_new == 0:
            S_i[SI_NEWEMPTY] += 1
            DY[d, DY_NEWEMPTY] = 1.0
    DY[d, DY_ARMUSE] = arm_use                # E6q：本臂票据总额（M1 / M2 / RANDOM_TARGET）→ TICKET_CONSERVATION
    extra_plan = 0.0
    if rtm == RT_NONE or nt == 0:
        for k in range(nt):
            s = tk_s[k]
            x = tk_x[k]
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
    # ---- RANDOM_TARGET：候选域与容量（无收益输入）
    nc = 0
    cs = np.empty(max(n, 1), np.int64)
    ccap = np.empty(max(n, 1))
    cgrp = np.empty(max(n, 1), np.int64)
    ckey = np.empty(max(n, 1))
    blk = (d + 1) // 5
    for k2 in range(a, b):
        s = f_col[k2]
        if not (f_w[k2] > 0.0):
            continue
        if rtm == RT_WITHIN and m1 and not isnew[s]:
            continue
        room = cap_s - expv[s]
        if m2:
            cr = capx[s] - (regbuy[s] - sellfix[s])
            if cr < 0.0:
                cr = 0.0
            room = min(room, cr)
        if not (room > 0.0):
            continue
        cs[nc] = s
        ccap[nc] = room
        cgrp[nc] = ind[d, s]
        ckey[nc] = hash_u(seed, blk, s)
        nc += 1
    grem = np.zeros(G)
    for g in range(G):
        r_ = (capsh[d, g] + idev) * NAVc - indsum[g]
        grem[g] = r_ if r_ > 0.0 else 0.0
    order = np.argsort(ckey[:nc], kind='mergesort')
    to = np.argsort(-tk_x[:nt], kind='mergesort')
    tick = np.empty(nt)
    for k in range(nt):
        tick[k] = tk_x[to[k]]
    tmax = tick[0]
    tmin = tick[nt - 1]
    identity = nt == nc and (tmax - tmin) <= 1e-12 * max(1.0, tmax)
    status = RTS_IDENTITY
    short = 0.0
    if identity:
        for k in range(nt):
            s = tk_s[k]
            x = tk_x[k]
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
        S_i[SI_RTID] += 1
    else:
        g2 = grem.copy()
        assign, status, nn = rt_match(tick, ccap[:nc], cgrp[:nc], g2, order, nodes)
        if status == RTS_FEASIBLE:
            for k in range(nt):
                ci = assign[k]
                s = cs[ci]
                x = tick[k]
                PB_i[npb, 0] = s
                PB_i[npb, 1] = 1
                PB_i[npb, 2] = -1
                PB_f[npb] = x
                expv[s] += x
                g = cgrp[ci]
                if g >= 0:
                    indsum[g] += x
                extra_plan += x
                npb += 1
        else:
            if status == RTS_LIMIT:
                S_i[SI_RTLIM] += 1
            else:
                S_i[SI_RTNOM] += 1
            # 调试缓冲（生产长度 1，不触发）：逐个追加未匹配实例（DBG[0] = 实例数、DBG[1] = 下一写入位置；块 = d, nt, nc, G, 状态, 票据, 票据原证券,
            # 候选余量, 候选行业, 优先序, 候选证券, 行业余量）
            need = 5 + 2 * nt + 4 * nc + G
            off = int(DBG[1]) if DBG.shape[0] > 2 else 0
            if off < 2:
                off = 2
            if DBG.shape[0] >= off + need:
                DBG[0] += 1.0
                DBG[off] = d
                DBG[off + 1] = nt
                DBG[off + 2] = nc
                DBG[off + 3] = G
                DBG[off + 4] = status
                DBG[1] = off + need
                p_ = off + 5
                for k in range(nt):
                    DBG[p_ + k] = tick[k]
                p_ += nt
                for k in range(nt):
                    DBG[p_ + k] = tk_s[to[k]]
                p_ += nt
                for k in range(nc):
                    DBG[p_ + k] = ccap[k]
                p_ += nc
                for k in range(nc):
                    DBG[p_ + k] = cgrp[k]
                p_ += nc
                for k in range(nc):
                    DBG[p_ + k] = order[k]
                p_ += nc
                for k in range(nc):
                    DBG[p_ + k] = cs[k]
                p_ += nc
                for g in range(G):
                    DBG[p_ + g] = grem[g]
            usedc = np.zeros(nc, np.bool_)
            g3 = grem.copy()
            for k in range(nt):
                t = tick[k]
                got = 0.0
                for oi in range(nc):
                    ci = order[oi]
                    if usedc[ci]:
                        continue
                    g = cgrp[ci]
                    room = ccap[ci]
                    if g >= 0 and g3[g] < room:
                        room = g3[g]
                    if not (room > 1e-15):
                        continue
                    got = t if t < room else room
                    usedc[ci] = True
                    s = cs[ci]
                    PB_i[npb, 0] = s
                    PB_i[npb, 1] = 1
                    PB_i[npb, 2] = -1
                    PB_f[npb] = got
                    expv[s] += got
                    if g >= 0:
                        indsum[g] += got
                        g3[g] -= got
                    extra_plan += got
                    npb += 1
                    break
                short += t - got
    DY[d, DY_RTST] = status
    DY[d, DY_RTSHORT] = short
    DY[d, DY_RTTK] = nt
    return npb, extra_plan
