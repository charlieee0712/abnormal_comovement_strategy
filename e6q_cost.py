# -*- coding: utf-8 -*-
"""E6q 成本仪器（plan §9.1 / §9.2；brief C5；附录 A-A）：
- curve（CURVE_IMPACT_FN，S0-A 选定的主仪器）：同一 NAV 节点 A_e = A0·n_e，Q_e = A_e·|Δw_e| = A0·dn / V0，冲击份额 = |Δw|·κσ√p0 (Q/(ADV·p0))^δ；
  引擎逐日系数 S_δ = Σ (dn / V⁺_{e−1}) σ √p0 (dn / (V0·ADV·p0))^δ（e6p_engine / e6q_engine cost_s05 / s07 / s10），固定路径份额 = κ A0^δ S_δ。
- legacy（LEGACY_IMPACT_FN，E6p LEGACY c5 的 D_imp）：κ √A Σ |Δw|^1.5 σ / √ADV，Δw = dn / V_pre（当日交易前 NAV），A 固定（不随 NAV 增长）。
- 单笔（附录 C cost / audit_cost 同式）：对数域计算防中间溢出；零订单 = 0（不需 σ / ADV）；非零订单缺 σ / ADV / ADV ≤ 0 → None（UNKNOWN，不填 0、不删股）；
  模型 0 波动 / κ = 0 → 0。"""
import math
import sys

import numpy as np

LOG_MAX = math.log(sys.float_info.max)
P0 = 0.01


def order_cost(q, adv, sigma, kappa=0.5, delta=0.5, p0=P0):
    """单笔货币冲击 C = |Q|·κσ√p0 (|Q| / (ADV·p0))^δ；返回 (值或 None, 状态)。状态 ∈ {ZERO_ORDER, MODEL_ZERO, COMPUTED, COST_MISSING, OUT_OF_NUMERICAL_RANGE}。"""
    q = abs(float(q))
    if q == 0.0:
        return 0.0, 'ZERO_ORDER'
    if sigma is None or adv is None or not math.isfinite(float(sigma)) or not math.isfinite(float(adv)) or float(adv) <= 0.0:
        return None, 'COST_MISSING'
    sigma = float(sigma)
    adv = float(adv)
    if sigma == 0.0 or kappa == 0.0:
        return 0.0, 'MODEL_ZERO'
    z = math.log(q) + math.log(kappa) + math.log(sigma) + 0.5 * math.log(p0) + delta * (math.log(q) - math.log(adv) - math.log(p0))
    if z > LOG_MAX:
        return None, 'OUT_OF_NUMERICAL_RANGE'
    return math.exp(z), 'COMPUTED'


def audit_share(dw, A, adv, sigma, kappa=0.5):
    """legacy 单笔份额 κ √A |Δw|^1.5 σ / √ADV（对数域）；同上状态。"""
    dw = abs(float(dw))
    if dw == 0.0:
        return 0.0, 'ZERO_ORDER'
    if sigma is None or adv is None or not math.isfinite(float(sigma)) or not math.isfinite(float(adv)) or float(adv) <= 0.0:
        return None, 'COST_MISSING'
    if float(sigma) == 0.0 or kappa == 0.0:
        return 0.0, 'MODEL_ZERO'
    z = math.log(kappa) + 0.5 * math.log(A) + 1.5 * math.log(dw) + math.log(float(sigma)) - 0.5 * math.log(float(adv))
    if z > LOG_MAX:
        return None, 'OUT_OF_NUMERICAL_RANGE'
    return math.exp(z), 'COMPUTED'


def curve_share_vec(dn, v_node, sigma, adv, A0, V0, kappa=0.5, delta=0.5, p0=P0):
    """向量化 curve 份额（同节点）：Σ_i (dn_i / v_node_i)·κσ_i√p0·(A0·dn_i / (V0·ADV_i·p0))^δ 的逐项值；缺 σ / ADV 的非零单 → NaN。"""
    dn = np.abs(np.asarray(dn, float))
    sg = np.asarray(sigma, float)
    av = np.asarray(adv, float)
    out = np.zeros_like(dn)
    nz = dn > 0
    ok = nz & np.isfinite(sg) & np.isfinite(av) & (av > 0)
    with np.errstate(all='ignore'):
        lz = (np.log(dn[ok]) - np.log(np.asarray(v_node, float)[ok]) + math.log(kappa) + np.log(np.where(sg[ok] > 0, sg[ok], 1.0)) + 0.5 * math.log(p0)
              + delta * (math.log(A0) + np.log(dn[ok]) - math.log(V0) - np.log(av[ok]) - math.log(p0)))
    v = np.exp(lz)
    v[sg[ok] == 0] = 0.0
    out[ok] = v
    out[nz & ~ok] = np.nan
    return out


def legacy_share_vec(dn, v_pre, sigma, adv, A, kappa=0.5):
    """向量化 legacy 份额：κ √A (dn / V_pre)^1.5 σ / √ADV 的逐项值；缺 σ / ADV 的非零单 → NaN。"""
    dn = np.abs(np.asarray(dn, float))
    sg = np.asarray(sigma, float)
    av = np.asarray(adv, float)
    out = np.zeros_like(dn)
    nz = dn > 0
    ok = nz & np.isfinite(sg) & np.isfinite(av) & (av > 0)
    with np.errstate(all='ignore'):
        lz = math.log(kappa) + 0.5 * math.log(A) + 1.5 * (np.log(dn[ok]) - np.log(np.asarray(v_pre, float)[ok])) + np.log(np.where(sg[ok] > 0, sg[ok], 1.0)) - 0.5 * np.log(av[ok])
    v = np.exp(lz)
    v[sg[ok] == 0] = 0.0
    out[ok] = v
    out[nz & ~ok] = np.nan
    return out


def fixed_path_share(S_delta, A0, kappa, delta):
    """固定路径日冲击份额 = κ A0^δ S_δ（S_δ = 引擎逐日系数）。"""
    return kappa * (A0 ** delta) * S_delta


def root_status(a, b, delta=0.5, A0=1e8):
    """plan §9.5：Δ(A) = a − b (A / A0)^δ 的过零点；a / b 异号或为 0 → NO_ROOT（不造正根）；负 → 正 = LOWER_CROSSING；浮点范围外 → OUT_OF_NUMERICAL_RANGE。"""
    if not (math.isfinite(a) and math.isfinite(b)):
        return None, 'COST_MISSING'
    if b == 0 or a == 0 or (a > 0) != (b > 0):
        return None, 'NO_ROOT'
    lr = math.log(A0) + (math.log(abs(a)) - math.log(abs(b))) / delta
    if lr > LOG_MAX or lr < math.log(sys.float_info.min):
        return None, 'OUT_OF_NUMERICAL_RANGE'
    return math.exp(lr), ('POSITIVE_ROOT' if a > 0 else 'LOWER_CROSSING')
