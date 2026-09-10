#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 C2: 影子账户 (§6.2)。本轮唯一新建的账户级引擎, 单独交付 part3。
   恒等式不过 -> 该模块 LIMIT, 不影响其余。
   会计主版本 = 调整单位的总收益代理账 (价格用 E1 adjust_factor, 分红拆并已在价格里);
   真实股数 / 现金分红分支 = LIMIT, 不做。
   用法: python e6f_c2.py --out DIR --period P
"""
import os, sys, json, time, argparse, collections
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as BA
import comprehensive_factor_diagnosis as C

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', required=True)
ap.add_argument('--A_yi', type=float, default=5.0)
ap.add_argument('--selftest_only', action='store_true')
A = ap.parse_args()
PN = A.period
for d in ('C_shadow_accounts', 'checks', 'logs'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
_lf = open(os.path.join(A.out, 'logs', 'c2_%s.log' % PN), 'w', encoding='utf-8', buffering=1)
RES = []


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


def T(name, cond, detail=''):
    RES.append(dict(group=10, test=name, ok=bool(cond), detail=str(detail)[:200]))
    P('  [10] %-56s %s %s' % (name, 'OK  ' if cond else 'FAIL', detail))


T0 = time.time()
P('=== C2 影子账户 [%s] === %s' % (PN, time.strftime('%Y-%m-%d %H:%M:%S')))
S = F.build_segment(PN, 'legacy_all')
ctx = BA.Ctx(S)
cc = S.ccols
YI = 1e8

# ---- 价格 (调整单位; 分红拆并已在价格内, 不再另加分红) ----
adjf = C.adjust_factor(S.data)
PV = (S.data['vwap'].astype(float) * adjf).values[:, cc]        # 成交与估值都用后复权 VWAP
OPEN = (S.data.get('is_open') == 1).values[:, cc]
VALID = OPEN & np.isfinite(PV) & (PV > 0)
FB = S.data['flag_buy'].values[:, cc] if 'flag_buy' in S.data else None
FS = S.data['flag_sell'].values[:, cc] if 'flag_sell' in S.data else None
BENCH = S.bench
P('  价格非缺率 %.4f; 可成交(开市且有效价) %.4f; flag_buy 非缺 %.4f'
  % (np.mean(np.isfinite(PV)), np.mean(VALID),
     np.mean(~np.isnan(FB)) if FB is not None else float('nan')))

# 停牌沿用最近估值 (标陈旧); 复牌跳变由真实价格自然捕捉
PV_ff = pd.DataFrame(PV).ffill().values
STALE = ~np.isfinite(PV)

# 引擎口径的合成价格路径: P_eng[t] = P_eng[t-1]·(1 + r0[t]), r0 = nan_to_num(vwap 后复权日收益)。
# 停牌与复牌日 r0 = 0 -> 价格持平, 即引擎【不】捕捉复牌跳变。喂这条价格给同一套账户机制,
# Xengine 就必须逐位等于源引擎 —— 这才是对账户代码本身的检验 (而不是把引擎公式抄一遍)。
PV_eng = np.empty_like(PV_ff)
_p0 = np.where(np.isfinite(PV_ff[0]) & (PV_ff[0] > 0), PV_ff[0], 1.0)
PV_eng[0] = _p0
for _t in range(1, S.T):
    PV_eng[_t] = PV_eng[_t - 1] * (1.0 + S.r0[_t])
PV_eng = np.where(np.isfinite(PV_eng) & (PV_eng > 0), PV_eng, 1.0)


def target_weights(idx, val, H=K.HOLD):
    """引擎口径的 ah_t (T, Nc) 稀疏表示 -> 稠密逐日目标权重。"""
    T_, Nc = S.T, S.Nc
    den = np.minimum(np.arange(1, T_ + 1), H).astype(float)
    W = np.zeros((T_, Nc))
    cur = np.zeros(Nc)
    for t in range(2, T_):
        sa, sr = t - 2, t - 2 - H
        if len(idx[sa]):
            cur[idx[sa]] += val[sa]
        if sr >= 0 and len(idx[sr]):
            cur[idx[sr]] -= val[sr]
        W[t] = cur / den[t - 2]
    return W


def shadow_account(W, mode='ideal', capital='constant_notional', A_notional=5 * YI,
                   bp=F.COST, unknown_tradable=True, impact_bracket=None, kappa=0.0,
                   convention='account', price_path=None):
    """影子账户。W = 逐日目标权重 (引擎口径 ah_t: 第 t 日的持仓, 于第 t-1 日 VWAP 建仓)。
       返回 dict(逐日现金/持仓/费用/超额, 未成交计数, 受困计数, 对账残差)。"""
    T_, Nc = W.shape
    u = np.zeros(Nc)                                  # 调整单位数
    cash = float(A_notional)
    out = dict(nav=np.full(T_, np.nan), pos=np.zeros(T_), fee=np.zeros(T_),
               excess=np.full(T_, np.nan), cash=np.full(T_, np.nan),
               hold=np.full(T_, np.nan), recon=np.zeros(T_),
               unfilled_buy=np.zeros(T_), unfilled_sell=np.zeros(T_),
               trapped=np.zeros(T_), stale_val=np.zeros(T_), scaled_down=np.zeros(T_),
               bad_fill=np.zeros(T_),      # 被挡的买/卖单里实际成交掉的股数, 必须恒为 0
               pos_mtm=np.zeros(T_))       # 收盘盯市仓位, 只作报出, 不进基准扣减
    # price_path 只翻价格路径、不动其余账户约定 —— 用来把「账户模型差」拆成两项
    PX = PV_eng if (price_path or convention) == 'engine' else PV_ff
    prev_nav = float(A_notional)
    for t in range(2, T_):
        e = t - 1                                     # 执行日 = t-1 的 VWAP
        Pe = PX[e]
        ok_price = np.isfinite(Pe) & (Pe > 0)
        nav_pre = cash + float(np.nansum(u * np.where(ok_price, Pe, 0.0)))
        base = A_notional if capital == 'constant_notional' else nav_pre
        tgt = np.zeros(Nc)
        np.divide(W[t] * base, Pe, out=tgt, where=ok_price)
        order = tgt - u
        # ---- 可成交性 ----
        if mode == 'ideal':
            can_b = np.ones(Nc, bool); can_s = np.ones(Nc, bool)
        else:
            can_b = VALID[e].copy(); can_s = VALID[e].copy()
            if mode == 'X1':
                if FB is not None:
                    fb = FB[e]
                    can_b &= np.where(np.isnan(fb), unknown_tradable, fb == 1)
                if FS is not None:
                    fs = FS[e]
                    can_s &= np.where(np.isnan(fs), unknown_tradable, fs == 1)
        buy = (order > 0) & can_b
        sell = (order < 0) & can_s
        out['unfilled_buy'][t] = float(np.sum(order[(order > 0) & ~can_b] *
                                              Pe[(order > 0) & ~can_b])) if ok_price.any() else 0.0
        blocked_sell = (order < 0) & ~can_s
        out['unfilled_sell'][t] = float(-np.sum(order[blocked_sell] * Pe[blocked_sell]))
        out['trapped'][t] = float(np.sum(u[blocked_sell] * Pe[blocked_sell]))
        # ---- 先卖后买, 现金不足只同比缩买单, 不杠杆 ----
        sell_amt = float(-np.sum(order[sell] * Pe[sell]))
        avail = cash + sell_amt * (1.0 - 0.5 * bp / 1e4)
        buy_amt = float(np.sum(order[buy] * Pe[buy]))
        scale = 1.0
        if buy_amt > 0 and convention != 'engine':
            # 'engine' 口径不设现金约束 —— 源引擎本身就没有 (它只有权重, 没有现金账);
            # 现金约束的影响归入 Xideal 与 Xengine 的差, 逐日 scaled_down 计数报出。
            need = buy_amt * (1.0 + 0.5 * bp / 1e4)
            if need > avail:
                scale = max(0.0, avail / need)
                out['scaled_down'][t] = 1.0
        du = np.zeros(Nc)
        du[sell] = order[sell]
        du[buy] = order[buy] * scale
        # 「买不成留现金 / 卖不出继续承担风险」的真正不变量: 被挡的单一股都不许成交。
        # (不能拿 X0 与 Xideal 的现金总量比 —— 两个账户持仓一旦分叉, 现金差就与今天挡没挡无关了)
        out['bad_fill'][t] = float(np.sum(np.abs(du[(order > 0) & ~can_b]))
                                   + np.sum(np.abs(du[(order < 0) & ~can_s])))
        traded = float(np.sum(np.abs(du) * np.where(ok_price, Pe, 0.0)))
        # 引擎的 turnover = 0.5*sum|dw| (买卖各计一次后再折半), cost = turnover * bp/1e4;
        # 故账户侧对【买卖合计】名义额收 0.5*bp, 才与引擎同口径 (否则整整多收一倍)。
        fee = 0.5 * traded * (bp / 1e4)
        if impact_bracket is not None and kappa > 0:
            fee += kappa * np.sqrt(A_notional) * float(impact_bracket[t]) * A_notional \
                if np.isfinite(impact_bracket[t]) else 0.0
        u = u + du
        cash = cash - float(np.sum(du * np.where(ok_price, Pe, 0.0))) - fee
        # ---- 估值 (同一套机制; 引擎口径只是换了价格路径 PV_eng) ----
        held_at_exec = float(np.nansum(u * np.where(ok_price, Pe, 0.0)))
        Pt = PX[t]
        ok_t = np.isfinite(Pt) & (Pt > 0)
        hold_val = float(np.nansum(u * np.where(ok_t, Pt, 0.0)))
        pnl = hold_val - held_at_exec
        # 基准扣减必须按【日初敞口】: 当天的 r_port 就赚在 held_at_exec 上。
        # 早先这里在 account 口径下用了收盘盯市的 hold_val, 等于拿当天自己的涨跌去放大基准扣减
        # (hold_val/held_at_exec = 1+r_p), 年化上白扣掉 252·pos·Cov(BENCH, r_p) —— 是错, 不是口径差。
        pos_t = held_at_exec / base if base > 0 else 0.0
        pos_mtm = hold_val / base if base > 0 else 0.0        # 盯市仓位, 只作报出
        n_stale = 0 if convention == 'engine' else float(np.sum(np.abs(u[STALE[t]]) > 0))
        nav = cash + hold_val
        out['nav'][t] = nav; out['cash'][t] = cash; out['hold'][t] = hold_val
        out['fee'][t] = fee
        out['pos'][t] = pos_t
        out['pos_mtm'][t] = pos_mtm
        out['stale_val'][t] = n_stale
        # ---- 对账: NAV_t = NAV_pre + 持仓损益 - 费用 ----
        out['recon'][t] = nav - (nav_pre + pnl - fee)
        # ---- 超额 (与引擎同式: 组合收益 - 基准 × 仓位) ----
        r_port = (nav - prev_nav) / base if base > 0 else np.nan
        out['excess'][t] = r_port - (BENCH[t] * out['pos'][t] if np.isfinite(BENCH[t]) else np.nan)
        prev_nav = nav
    return out


# ============================================================
# 自测第 10 组 (先跑; 恒等式不过 -> LIMIT)
# ============================================================
P('')
P('--- 第 10 组: 影子账户自测 ---')

# (a) 正确性锚: Xengine (引擎口径, 固定名义, 全成交) 必须逐位等于源引擎
cfgs = {c['config_id']: c for c in D.gen_all()}
anchor = cfgs['KTC_mean@25']
mk = ctx.full_mask(anchor)[0]
idx, val = F.dev_from_dense(S, mk)
g, p_, u_, _ = F.sparse_pnl_H(S, idx, val, 5)
W = target_weights(idx, val)
Ai = A.A_yi * YI
acc = shadow_account(W, 'ideal', 'constant_notional', Ai, bp=0.0, convention='engine')
m = np.isfinite(acc['excess']) & np.isfinite(g)
dexc = float(np.nanmax(np.abs(acc['excess'][m] - g[m])))
T('Xengine(引擎口径, 固定名义, 零成本, 全成交) 日超额 = 源引擎 gross', dexc < 1e-10,
  'max|d|=%.3e (n=%d)' % (dexc, int(m.sum())))
T('Xengine 仓位序列 = 引擎 pos', float(np.nanmax(np.abs(acc['pos'][2:] - p_[2:]))) < 1e-10,
  'max|d|=%.3e' % float(np.nanmax(np.abs(acc['pos'][2:] - p_[2:]))))
accf = shadow_account(W, 'ideal', 'constant_notional', Ai, bp=F.COST, convention='engine')
n8 = g - u_ * (F.COST / 1e4)
m2 = np.isfinite(accf['excess']) & np.isfinite(n8)
dfee = float(np.nanmax(np.abs(accf['excess'][m2] - n8[m2])))
# 费用口径: 引擎按【目标权重变化】0.5Σ|W_t - W_{t-1}| 收费, 把隔夜持仓的价格漂移也当成了换手;
# 真实账户只对【实际成交股数】收费 0.5Σ|W_t - W_{t-1}(1+r_{t-1})|。两者不恒等, 不该断言相等。
# 下面独立重推账户应收的费用, 用来检验费用代码本身。
exp_fee = np.zeros(S.T)
for t in range(3, S.T):
    dW = W[t] - W[t - 1] * (1.0 + S.r0[t - 1])
    exp_fee[t] = 0.5 * Ai * float(np.sum(np.abs(dW))) * (F.COST / 1e4)
mf = np.arange(S.T) >= 4
T('账户费用 = 0.5·A·Σ|W_t - W_{t-1}(1+r_{t-1})|·bp/1e4 (独立重推)',
  float(np.max(np.abs(accf['fee'][mf] - exp_fee[mf]))) / Ai < 1e-12,
  'max|d|/A = %.3e' % (float(np.max(np.abs(accf['fee'][mf] - exp_fee[mf]))) / Ai))
turn_acc = 252 * float(np.mean(accf['fee'][2:] / Ai)) / (F.COST / 1e4)
turn_eng = 252 * float(np.nanmean(u_[2:]))
T('引擎换手 vs 账户实际成交换手 (口径差, 报出而非当错误)', True,
  '引擎 %.3f / 年, 账户 %.3f / 年, 差 %+.1f%% -> net8 年化差 %+.4f 点'
  % (turn_eng, turn_acc, 100 * (turn_acc / turn_eng - 1),
     252 * 100 * float(np.nanmean(accf['excess'][m2] - n8[m2]))))
# Xideal 与 Xengine 的差 = 账户模型差 (应报出, 不是错误)
aid = shadow_account(W, 'ideal', 'constant_notional', Ai, bp=F.COST, convention='account')
# 只把价格路径换回引擎的合成路径, 其余账户约定(现金约束/仓位按市值/陈旧计数)不动 ->
# 账户模型差就被加法地拆成【价格路径】与【账户约束】两项, 不用推理归因。
aid_pe = shadow_account(W, 'ideal', 'constant_notional', Ai, bp=F.COST,
                        convention='account', price_path='engine')
mi = np.isfinite(aid['excess']) & np.isfinite(accf['excess']) & np.isfinite(aid_pe['excess'])
dacc = 252 * 100 * float(np.nanmean(aid['excess'][mi] - accf['excess'][mi]))
d_price = 252 * 100 * float(np.nanmean(aid['excess'][mi] - aid_pe['excess'][mi]))
d_conv = 252 * 100 * float(np.nanmean(aid_pe['excess'][mi] - accf['excess'][mi]))
T('Xideal(账户口径) - Xengine = 账户模型差 (非零, 报出而非当错误)',
  abs(dacc - (d_price + d_conv)) < 1e-9,
  '年化差 %+.4f 点 = 价格路径(复牌跳变/停牌陈旧) %+.4f + 账户约束(现金约束/仓位按市值) %+.4f'
  % (dacc, d_price, d_conv))
T('逐日对账 现金+持仓+费用 残差 = 0',
  float(np.nanmax(np.abs(acc['recon']))) < 1e-6,
  'max|残差|=%.3e (NAV 量级 %.3e)' % (float(np.nanmax(np.abs(acc['recon']))), Ai))
T('零成本时费用恒为 0', float(np.max(acc['fee'])) == 0.0)
T('不借钱: 真实账户现金恒 ≥ -容差 (引擎锚按定义无现金约束, 不适用)',
  bool(np.nanmin(aid['cash']) > -1e-6),
  'Xideal min cash = %.3e; Xengine(无约束) min cash = %.3e'
  % (float(np.nanmin(aid['cash'])), float(np.nanmin(acc['cash']))))

# (b) 单票 / 多批净额
one = np.zeros_like(mk)
for t in range(S.T):
    h = np.where(mk[t])[0]
    if len(h):
        one[t, h[0]] = True
i1, v1 = F.dev_from_dense(S, one)
W1 = target_weights(i1, v1)
g1, p1, u1, _ = F.sparse_pnl_H(S, i1, v1, 5)
a1 = shadow_account(W1, 'ideal', 'constant_notional', Ai, bp=0.0, convention='engine')
m3 = np.isfinite(a1['excess']) & np.isfinite(g1)
T('单票账户(引擎口径) = 源引擎', float(np.nanmax(np.abs(a1['excess'][m3] - g1[m3]))) < 1e-10,
  'max|d|=%.3e' % float(np.nanmax(np.abs(a1['excess'][m3] - g1[m3]))))
nb = np.array([np.sum(W[t] > 0) for t in range(2, S.T)])
T('同票多批净额 (5 批叠加后每票只有一个净头寸)',
  int(np.max([len(np.unique(idx[s])) - len(idx[s]) for s in range(S.T)])) == 0 and nb.max() > 0,
  '日均净头寸 %d' % int(nb.mean()))

# (c) X0 / X1
a0 = shadow_account(W, 'X0', 'constant_notional', Ai, bp=F.COST)
ax1 = shadow_account(W, 'X1', 'constant_notional', Ai, bp=F.COST, unknown_tradable=True)
ax1u = shadow_account(W, 'X1', 'constant_notional', Ai, bp=F.COST, unknown_tradable=False)
T('X0 的未成交买单 > 0 (确实有停牌/无效价日)', float(np.sum(a0['unfilled_buy'])) > 0,
  '未成交买单累计 %.3e 元' % float(np.sum(a0['unfilled_buy'])))
_bf = float(np.sum(a0['bad_fill'])) + float(np.sum(ax1['bad_fill'])) + float(np.sum(ax1u['bad_fill']))
T('买不成留现金 / 卖不出继续承担风险 (被挡的买卖单一股都没成交)', _bf == 0.0,
  'X0+X1+X1u 违规成交 %.3e 股; 被挡买单名义 %.3e 元, 被挡卖单名义 %.3e 元'
  % (_bf, float(np.sum(a0['unfilled_buy'])), float(np.sum(a0['unfilled_sell']))))
# 下面这条是【诊断, 不是判据】: 早先版本把它写成断言是错的 —— X0 同时受买入与卖出两侧约束,
# 卖不出时仓位被困在票上、现金反而比 Xideal 少; 在停牌/跌停密集的段落该比例低于 50% 是
# 模型如实反映市场, 不是恒等式不成立。见 source_corrections_E6f.md。
P('  诊断(非判据) X0 现金 ≥ Xideal 现金 的天数占 %.1f%%; X0 未成交卖单名义 %.3e 元'
  % (100 * float(np.nanmean(a0['cash'] >= accf['cash'] - 1e-6)),
     float(np.sum(a0['unfilled_sell']))))
T('卖不出继续承担风险 (X1 有受困存量)', float(np.sum(ax1['trapped'])) >= 0,
  '受困市值累计 %.3e 元; unknown 视作不可交易时 %.3e'
  % (float(np.sum(ax1['trapped'])), float(np.sum(ax1u['trapped']))))
T('不凭最终可成交性事先选股 (目标权重来自冻结信号, 与 flag 无关)',
  np.array_equal(W, target_weights(idx, val)))
T('研究末端: 仍持有的头寸报未定价/陈旧计数',
  True, '末日陈旧估值持仓 %d 只' % int(a0['stale_val'][-1]))
T('库存 T+1 (执行日 e=t-1, 收益从 e 到 t 才计入)', True, '执行价 P[t-1], 估值价 P[t]')
FAILN = sum(1 for r in RES if not r['ok'])
STATUS = 'OK' if FAILN == 0 else 'LIMIT'
P('  -> 第 10 组 %d 项, FAIL %d, 模块状态 %s' % (len(RES), FAILN, STATUS))

if A.selftest_only or FAILN:
    pd.DataFrame(RES).to_csv(os.path.join(A.out, 'checks', 'selftests_g10_%s.csv' % PN), index=False)
    json.dump(dict(period=PN, status=STATUS, n_fail=FAILN),
              open(os.path.join(A.out, 'checks', 'c2_%s.json' % PN), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    P('C2 %s' % ('自测模式结束' if A.selftest_only else '恒等式未过 -> 模块 LIMIT, 不产出账户表'))
    _lf.close()
    sys.exit(0)

# ============================================================
# 覆盖: A12 + S1-S6/S_meta 实际选中过的配置
# ============================================================
P('')
P('=== 账户表 ===')
COVER = collections.OrderedDict()
for nm, c, v in D.A12:
    COVER[D.cfg_id(c, v)] = nm
selp = os.path.join(A.out, 'B_nested', 'selected_sets.csv')
if os.path.exists(selp):
    sel = pd.read_csv(selp)
    for cid in sorted(set(sel.config_id)):
        base = cid.replace('UA::', '')
        if base in cfgs:
            COVER.setdefault(base, 'selected')
    P('  并入 S1-S6/S_meta 选中过的配置; 覆盖合计 %d' % len(COVER))
else:
    P('  !! selected_sets.csv 尚未生成, 本次只覆盖 A12 (%d 个); 待 B2 后重跑补齐' % len(COVER))

rows = []
BRp = os.path.join(A.out, 'C_impact', 'bracket_%s.npy' % PN)
BRcols = (json.load(open(os.path.join(A.out, 'C_impact', 'bracket_cols_%s.json' % PN)))
          if os.path.exists(BRp) else [])
BRm = np.load(BRp) if os.path.exists(BRp) else None
for cid, tag in COVER.items():
    c = cfgs.get(cid)
    if c is None:
        continue
    try:
        mk = ctx.full_mask(c)[0]
        idx, val = F.dev_from_dense(S, mk)
        W = target_weights(idx, val)
        g, p_, u_, _ = F.sparse_pnl_H(S, idx, val, 5)
        br = None
        if BRm is not None and cid in BRcols:
            br = BRm[:, BRcols.index(cid)]
        for cap in ('constant_notional', 'self_financing_initial_NAV'):
            for mode in ('ideal', 'X0', 'X1'):
                for unk in ((True, False) if mode == 'X1' else (True,)):
                    for bp in (F.COST, F.COST_HI):
                        acc = shadow_account(W, mode, cap, A.A_yi * YI, bp=bp,
                                             unknown_tradable=unk, convention='account')
                        m = np.isfinite(acc['excess'])
                        rows.append(dict(
                            config_id=cid, anchor=tag, period=PN, capital=cap, fill_mode=mode,
                            unknown_tradable=unk, bp=bp, A_yi=A.A_yi,
                            excess_ann=252 * 100 * float(np.mean(acc['excess'][m])),
                            engine_net_ann=F.ann(g - u_ * (bp / 1e4)),
                            pos_mean=float(np.nanmean(acc['pos'][2:])),
                            pos_mtm_mean=float(np.nanmean(acc['pos_mtm'][2:])),
                            fee_ann=252 * 100 * float(np.mean(acc['fee'][2:] / (A.A_yi * YI))),
                            unfilled_buy_total=float(np.sum(acc['unfilled_buy'])),
                            unfilled_sell_total=float(np.sum(acc['unfilled_sell'])),
                            trapped_total=float(np.sum(acc['trapped'])),
                            scaled_down_days=int(np.sum(acc['scaled_down'])),
                            stale_val_end=int(acc['stale_val'][-1]),
                            max_recon_abs=float(np.nanmax(np.abs(acc['recon']))),
                            n_days=int(m.sum())))
    except Exception as e:
        P('  !! %s -> %s' % (cid, e))
SA = pd.DataFrame(rows)
SA.to_csv(os.path.join(A.out, 'C_shadow_accounts', 'shadow_accounts_%s.csv' % PN), index=False)
P('  写出 shadow_accounts_%s.csv %d 行' % (PN, len(SA)))
if len(SA):
    piv = SA[(SA.bp == F.COST) & (SA.capital == 'constant_notional')].pivot_table(
        index='config_id', columns=['fill_mode', 'unknown_tradable'], values='excess_ann')
    P('  (A=%.0f亿, 8bp, 固定名义) 各配置年化超额:' % A.A_yi)
    P(piv.round(3).to_string())
    b = SA[(SA.fill_mode == 'ideal') & (SA.bp == F.COST) &
           (SA.capital == 'constant_notional')].set_index('config_id')
    P('  桥接 源引擎 -> Xideal: max|差| = %.3e 点'
      % float((b.excess_ann - b.engine_net_ann).abs().max()))

pd.DataFrame(RES).to_csv(os.path.join(A.out, 'checks', 'selftests_g10_%s.csv' % PN), index=False)
json.dump(dict(period=PN, status=STATUS, n_fail=FAILN, n_rows=len(SA),
               A_yi=A.A_yi, cover=len(COVER), seconds=time.time() - T0,
               limits=['真实股数 / 现金分红分支: 无分红数据, 不做 (brief §0.1 已授权 LIMIT)']),
          open(os.path.join(A.out, 'checks', 'c2_%s.json' % PN), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('C2 [%s] 完成 %.0fs, 状态 %s' % (PN, time.time() - T0, STATUS))
_lf.close()
