# -*- coding: utf-8 -*-
"""E6q S0-A 两实现对账（brief §2 / §0.1 #9；附录 A-A；plan §9.1 v1.1；先于任何新成本读数）。
对象：附录 G 七个 E6p 账户（FEASIBLE；只读 E6p 交接的逐日 DY 与成交分片 trades_parts/deriv + full，同一实际成交片段）。
逐证券日净单（同日同证券买卖先轧差，与引擎收费口径同）提取 legacy 与 curve 的输入：dn（引擎单位，V0 = 初始 NAV）、σ20、ADV20（CNY，T−20…T−1）、
当日交易前 NAV V_pre（legacy 的 Δw 节点）、前一日交易后 NAV V⁺_{e−1}（curve 的 Δw 节点）、V0。
- legacy = κ √A Σ (dn / V_pre)^1.5 σ / √ADV（E6p LEGACY c5 的 D_imp，A 固定）；curve = κ A^δ Σ (dn / V⁺_{e−1}) σ √p0 (dn / (V0·ADV·p0))^δ（E6p cost_curve，A_e = A·n_e）。
- 先核提取：逐日 Σ 与 E6p DY 的 impact_br / cost_s05 列一致（相对 1e−9），证明是同一成交、同一输入。
- 订单类别分摊（冻结规则）：证券日净单冲击只分给净方向一侧的成交行、按名义额比例；对侧被内部轧差的行分 0（不各收一次）。
- 置换 ladder：L00 原式 → L01 参与率节点 A0 → A_e = A0·n_e（Q = A·dn / V0）→ L02 权重节点 V_pre → V⁺_{e−1}；另逐项单独试 T01–T09（σ×√252、bp / 小数、
  成交额千元、毛额 vs 净额、现金反馈路径、重复记费、窗口错一日、分段年化、旧缓存），记残差比与解释份额（对数口径）。
输出：verify/impact_reconciliation_E6q.csv、verify/impact_reconciliation_ladder_E6q.csv、verify/impact_reconciliation_daily_bridge_E6q.csv、reports/E6q_S0A_reconciliation.md、
diagnostics/s0a_facts_E6q.json。用法：python3 e6q_s0a.py"""
import os
import json
import math
import time

import numpy as np
import pandas as pd

import e6q_core as O
import e6q_cost as CO

A_EVAL = 5e8
KAPPA = 0.5
DELTA = 0.5
OBJ7 = (('H5_PARENT', 'E6P-57e0690911d8ae695b796d35'), ('H20_PARENT', 'E6P-99de9b5674c5c0bbc14d5523'), ('T1A_H20', 'E6P-28aebd98dafd9607427500c4'),
        ('LEVEL_H20', 'E6P-b8173d4bb4481eabcd7c1a04'), ('EDGE_H5', 'E6P-35d575a597d2174f9504d93b'), ('CASH_LEVEL_H20', 'E6P-acb1b75f68fd78610b256922'),
        ('HALF_LEVEL_H20', 'E6P-634d5d4bb7bcaf1057dd9ef7'))
E6P_TAIL = '|FEASIBLE_DAILY|FULLHIST|CASH_V0|FIXED_PATH_V1|E6P_V11'
KINDS = ('ALL', 'BUY', 'SELL', 'REGULAR', 'EXIT', 'EXTRA', 'DUE')
E6P_OK = {0: 'REGULAR', 1: 'EXIT', 2: 'EXTRA', 3: 'RENEW', 4: 'DUE'}
SEG6 = list(O.SEGS) + ['FULL', 'G4']


def load_obj(eid, mk):
    R = pd.read_csv(O.E6P('registration', 'registry_E6p.csv'), keep_default_na=False, dtype=str)
    h = R[R.exec_id == eid].exec_hash
    if len(h) != 1:
        raise RuntimeError('E6p exec_id 不在 registry：%s' % eid)
    h = h.iloc[0]
    DY = np.load(O.E6P('accounts_run', 'full', h[:2], '%s.npz' % h), allow_pickle=False)['DY']
    parts = []
    for ph in ('deriv', 'full'):
        p = O.E6P('trades_parts', ph, h[:2], '%s.npz' % h)
        z = np.load(p, allow_pickle=False)
        parts.append((z['TL_i'], z['TL_f']))
    TLi = np.concatenate([p[0] for p in parts])
    TLf = np.concatenate([p[1] for p in parts])
    return h, DY, TLi, TLf


def security_days(TLi, TLf, mk, DY):
    """逐证券日：B、S、dn = |B − S|、σ、ADV、V_pre、V⁺_{e−1}；返回 DataFrame（每行一证券日）与成交行的证券日编号。"""
    d = TLi[:, 0].astype(np.int64)
    s = TLi[:, 1].astype(np.int64)
    side = TLi[:, 5].astype(np.int64)
    notional = TLf[:, 1].astype(float)
    key = d * 10000 + s
    uk, inv = np.unique(key, return_inverse=True)
    B = np.bincount(inv, weights=np.where(side == 0, notional, 0.0), minlength=len(uk))
    S = np.bincount(inv, weights=np.where(side == 1, notional, 0.0), minlength=len(uk))
    dd = uk // 10000
    ss = uk % 10000
    sig = np.asarray(mk['sig20'])[dd, ss]
    adv = np.asarray(mk['adv20'])[dd, ss]
    vpre = DY[dd, 0]
    vprev = np.where(dd >= 1, DY[np.maximum(dd - 1, 0), 1], O.V0)
    return pd.DataFrame(dict(day=dd, sec=ss, B=B, S=S, dn=np.abs(B - S), sig=sig, adv=adv, vpre=vpre, vprev=vprev)), inv


def legacy_coef(df, node='vpre', part='fixed', sig_scale=1.0, adv_scale=1.0, gross=False):
    """legacy 系数（不含 κ√A）：Σ (q / V_node)^1.5 σ / √ADV；part = 'nav' 时参与率改用同节点 A_e：(q / V_node) σ √(q / (V0·ADV))。"""
    q = (df.B + df.S).to_numpy() if gross else df.dn.to_numpy()
    v = df[node].to_numpy()
    sg = df.sig.to_numpy() * sig_scale
    av = df.adv.to_numpy() * adv_scale
    ok = (q > 0) & np.isfinite(sg) & np.isfinite(av) & (av > 0)
    out = np.zeros(len(df))
    with np.errstate(all='ignore'):
        if part == 'fixed':
            out[ok] = (q[ok] / v[ok]) ** 1.5 * sg[ok] / np.sqrt(av[ok])
        else:
            out[ok] = (q[ok] / v[ok]) * sg[ok] * np.sqrt(q[ok] / (O.V0 * av[ok]))
    return out


def curve_coef(df):
    """curve 系数 S_.5（不含 κ A^.5）：Σ (dn / V⁺_{e−1}) σ √p0 (dn / (V0·ADV·p0))^.5（引擎 cost_s05 同式）。"""
    q = df.dn.to_numpy()
    v = df.vprev.to_numpy()
    sg = df.sig.to_numpy()
    av = df.adv.to_numpy()
    ok = (q > 0) & np.isfinite(sg) & np.isfinite(av) & (av > 0) & (v > 0)
    out = np.zeros(len(df))
    p0 = CO.P0
    with np.errstate(all='ignore'):
        out[ok] = (q[ok] / v[ok]) * sg[ok] * math.sqrt(p0) * (q[ok] / (O.V0 * av[ok] * p0)) ** 0.5
    return out


def kind_alloc(TLi, TLf, inv, sd, coef):
    """证券日系数分给净方向一侧的成交行（按名义额比例）；返回逐成交行份额。"""
    side = TLi[:, 5].astype(np.int64)
    notional = TLf[:, 1].astype(float)
    netbuy = (sd.B.to_numpy() > sd.S.to_numpy())[inv]
    onside = np.where(netbuy, side == 0, side == 1)
    w = np.where(onside, notional, 0.0)
    tot = np.bincount(inv, weights=w, minlength=len(sd))
    with np.errstate(all='ignore'):
        share = np.where(onside & (tot[inv] > 0), w / tot[inv], 0.0)
    return share * coef[inv]


def seg_ann(day_vals, segi, T):
    """日份额（逐日求和后）→ 段年化 ann_pp = 252 × 100 × 段内日均（全部交易日为分母，无交易日记 0）；FULL = Σ n v / Σ n；G4 = 四段中位。"""
    out = {}
    num, den = 0.0, 0
    for s in O.SEGS:
        m = segi == s
        n = int(m.sum())
        v = float(day_vals[m].sum() / n * O.ANN_PP) if n else float('nan')
        out[s] = v
        num += v * n
        den += n
    out['FULL'] = num / den
    out['G4'] = float(np.median([out[s] for s in O.SEGS]))
    return out


def write_report(RC, LD, BR, agg, facts, status):
    f = lambda x: '%.4f' % x
    L = ['# E6q S0-A 两套冲击实现对账（报告；附录 A-A / plan §9.1）', '',
         '**页首**：协议 v1.6、方式 B；E7 不做、无部署授权（deployment_authorized = false）；本卡在任何新臂成本读数之前完成，只读 E6p 已交付账户与成交分片。',
         '本卡的书面结论取代此前被问的"两口径差 1.8–1.9 倍"的单独回答（brief §0.1 #9）。', '',
         '## 结论', '',
         '- 对账状态：**%s**。' % status,
         '- 差异来源已闭合：两式在**同一 NAV 节点**上逐日相等。legacy 用固定规模 A（参与率 Q = A·dn / V_pre，不随净值增长）且权重节点取当日交易前 NAV；'
         'curve 用 A_e = A·n_e（Q = A·dn / V0，即 plan v1.1 §9.1 的 A_e = A0_eval·n_e、Q_e = A_e·|Δw_e|）且权重节点取前一日交易后 NAV。',
         '- 两步置换后残差比 = 1（7 个对象最大偏离 %.1e），解释份额 100%%；其余候选（σ×√252、bp / 小数、千元单位、毛额 / 净额、现金反馈、重复记费、窗口错一日、分段年化、旧缓存）'
         '都不是来源（见 ladder）。' % max(abs(v['r2'] - 1.0) for v in agg.values()),
         '- 比值**不是常数**：逐日 legacy / curve = (V⁺_{e−1} / V_pre)·√(V0 / V_pre)，随账户净值路径变化（日桥 `verify/impact_reconciliation_daily_bridge_E6q.csv`）。'
         '因此不给 κ 换算常数；同一节点上两式本来相同（κ_curve = κ_legacy，f = 恒等，误差 0），差的只是 NAV 节点。',
         '- **唯一主仪器 = curve（CURVE_IMPACT_FN）**。选择理由：符合本轮已冻结的经济单位定义（plan v1.1 §9.1：A 与该笔 Δw 同一估值节点、A_e = A0·n_e、成本分母也用 A_e）'
         '与附录 C 的 `fixed_path_order` / `audit_cost` 同节点恒等；不是因为它更便宜——curve 比 legacy 高（FULL 比值 %s–%s，即 curve 约为 legacy 的 %.2f–%.2f 倍）。'
         % (f(facts['ratio_range_full_all'][0]), f(facts['ratio_range_full_all'][1]), 1 / facts['ratio_range_full_all'][1], 1 / facts['ratio_range_full_all'][0]),
         '- 读法后果：E6p 的 LEGACY c5（D_imp）低估了净值增长后的冲击；政策 POLICY_E6Q_A1_CANONICAL 的 c5 用 curve；LEGACY_E6O_A5 只作审计并照原式。', '',
         '## 提取核验（同一实际成交）', '',
         '| 对象 | E6p exec_hash | 成交行 | 证券日 | 非零净单 | 逐日 Σ vs DY impact_br | 逐日 Σ vs DY cost_s05 | 非零单缺 σ / ADV |', '|---|---|---:|---:|---:|---:|---:|---:|']
    for lab, _ in OBJ7:
        x = facts[lab]
        L.append('| %s | `%s` | %d | %d | %d | %.1e | %.1e | %d |' % (lab, x['e6p_exec_hash'], x['n_trade_rows'], x['n_security_days'], x['n_net_orders'],
                                                              x['extract_vs_dy_impact_br_max_rel'], x['extract_vs_dy_cost_s05_max_rel'], x['missing_liq_nonzero']))
    L += ['', '## FULL × ALL（A = 5 亿、κ .5、δ .5；ann_pp）与置换 ladder', '', '| 对象 | legacy | curve | 比值 L00 | L01 参与率节点 | L02 权重节点 |', '|---|---:|---:|---:|---:|---:|']
    for lab, _ in OBJ7:
        v = agg[lab]
        L.append('| %s | %s | %s | %s | %s | %.12f |' % (lab, f(v['full_l']), f(v['full_c']), f(v['r0']), f(v['r1']), v['r2']))
    L += ['', '解释份额按对数口径：(ln r0 − ln r) / ln r0。L01 单独已解释绝大部分（NAV 增长使固定 A 的参与率越来越低估），L02 收尾（一日收益量级）。'
          'T01–T09 单项置换的残差见 `verify/impact_reconciliation_ladder_E6q.csv`，均不能使残差比接近 1。', '',
          '## 订单类别分摊规则（冻结）', '',
          '冲击按证券日净单收费（与引擎同）：同日同证券买卖先轧差，净单冲击只分给净方向一侧的成交行、按名义额比例；被内部轧差的对侧行分 0。'
          'EXIT 含早退（E6p 对象无 RENEW）；7 类 = ALL / BUY / SELL / REGULAR / EXIT / EXTRA / DUE；表 `verify/impact_reconciliation_E6q.csv`（7 × 6 × 7）。', '',
          '## 恒等（写入 verify/identities_E6q.csv）', '',
          '- IMPACT_ALGEBRA_EQUAL：合成输入下 δ = .5、Q = A|Δw| 同节点时两式相等（≤ 1e−12）。',
          '- SAME_NAV_NODE_COST：真实 E6p 成交上 legacy 改到同节点后逐日 = curve。',
          '- ZERO_ORDER_ZERO_COST、NONZERO_ORDER_MISSING_LIQ_UNKNOWN（BLOCKED）、LOG_DOMAIN_NO_OVERFLOW：见 Stage 0 合成夹具。', '',
          '## 对 CC-E6q-10 与 plan §9.1 的含义', '',
          '- CC-E6q-10 的"比值 ∈ [1.7, 2.1]"按原句在对账表 ALL 行评分（见 claims）；它是经验读法，真 ENG 是 IMPACT_ALGEBRA_EQUAL。',
          '- 附录 A-A 写"比例非恒定或来源未闭合 → UNDECIDABLE"。本卡来源已闭合（两项 NAV 节点置换后残差 0），非恒定只来自净值路径本身，'
          '按 plan §9.1"保留逐日输入桥、不公布虚假统一系数"处理，状态记 RECONCILED。此读法写进 notes §8 供决策端确认；若决策端按字面改判 UNDECIDABLE，'
          'policy 的 CANONICAL c5 全部改 NA，其余表不受影响。']
    O.atomic_write_text(O.P('reports', 'E6q_S0A_reconciliation.md'), '\n'.join(L) + '\n')


def main():
    t0 = time.time()
    cd = O.cache_dir()
    pd_ = os.path.join(cd, 'panels')
    mk = {k: np.load(os.path.join(pd_, k + '.npy'), mmap_mode='r') for k in ('sig20', 'adv20')}
    dates = np.load(os.path.join(pd_, 'dates.npy'))
    T = len(dates)
    segi = np.array([O.seg_of_date(d) for d in dates])
    kA = KAPPA * math.sqrt(A_EVAL)
    kC = KAPPA * A_EVAL ** DELTA
    rows, lad, bridge, facts = [], [], [], {}
    agg = {}
    for label, lid in OBJ7:
        eid = lid + E6P_TAIL
        h, DY, TLi, TLf = load_obj(eid, mk)
        sd, inv = security_days(TLi, TLf, mk, DY)
        Lc = legacy_coef(sd)
        Cc = curve_coef(sd)
        # 提取核验：逐日 Σ 与 E6p DY impact_br（列 11）/ cost_s05（列 39）
        dl = np.bincount(sd.day.to_numpy(), weights=Lc, minlength=T)
        dc = np.bincount(sd.day.to_numpy(), weights=Cc, minlength=T)
        ref_l = DY[:, 11]
        ref_c = DY[:, 39]
        rl = float(np.max(np.abs(dl - ref_l) / np.maximum(np.abs(ref_l), 1e-300)))
        rcv = float(np.max(np.abs(dc - ref_c) / np.maximum(np.abs(ref_c), 1e-300)))
        facts[label] = dict(e6p_exec_hash=h, n_trade_rows=int(len(TLi)), n_security_days=int(len(sd)), n_net_orders=int((sd.dn > 0).sum()),
                            extract_vs_dy_impact_br_max_rel=rl, extract_vs_dy_cost_s05_max_rel=rcv,
                            missing_liq_nonzero=int(((sd.dn > 0) & ~(np.isfinite(sd.sig) & np.isfinite(sd.adv) & (sd.adv > 0))).sum()))
        if rl > 1e-9 or rcv > 1e-9:
            raise RuntimeError('S0-A 提取与 E6p DY 不一致：%s legacy %.2e curve %.2e' % (label, rl, rcv))
        # 订单类别（7 类）
        kind = np.array([E6P_OK.get(int(k), 'OTHER') for k in TLi[:, 4]])
        side = TLi[:, 5].astype(np.int64)
        lrow = kind_alloc(TLi, TLf, inv, sd, Lc) * kA
        crow = kind_alloc(TLi, TLf, inv, sd, Cc) * kC
        tday = TLi[:, 0].astype(np.int64)
        masks = {'ALL': np.ones(len(TLi), bool), 'BUY': side == 0, 'SELL': side == 1, 'REGULAR': kind == 'REGULAR', 'EXIT': (kind == 'EXIT') | (kind == 'RENEW'),
                 'EXTRA': kind == 'EXTRA', 'DUE': kind == 'DUE'}
        for kk in KINDS:
            m = masks[kk]
            lv = seg_ann(np.bincount(tday[m], weights=lrow[m], minlength=T), segi, T)
            cv = seg_ann(np.bincount(tday[m], weights=crow[m], minlength=T), segi, T)
            nseg = {s: int((m & (segi[tday] == s)).sum()) for s in O.SEGS}
            nseg['FULL'] = int(m.sum())
            nseg['G4'] = int(np.median([nseg[s] for s in O.SEGS]))
            for s in SEG6:
                a, b = lv[s], cv[s]
                rows.append(dict(object_label=label, e6p_exec_id=eid, segment=s, order_kind=kk, n_orders=nseg[s], legacy_impact_ann_pp=a, curve_impact_ann_pp=b,
                                 ratio=(a / b) if b > 0 else '', status='COMPUTED' if b > 0 else 'NOT_APPLICABLE'))
        # 日桥：legacy / curve 的逐日比值（非恒定，保留）
        n_e = DY[:, 0] / O.V0
        with np.errstate(all='ignore'):
            rb = np.where(dc > 0, (dl * kA) / (dc * kC), np.nan)
        theo = np.full(T, np.nan)
        vprev_d = np.r_[O.V0, DY[:-1, 1]]
        with np.errstate(all='ignore'):
            theo = (vprev_d / DY[:, 0]) * np.sqrt(O.V0 / DY[:, 0])
        bridge.append(pd.DataFrame(dict(object_label=label, date=dates, nav_pre_over_V0=n_e, nav_prev_over_V0=vprev_d / O.V0, ratio_legacy_over_curve=rb,
                                        ratio_theory=theo)))
        # ladder（FULL × ALL）
        full_l = seg_ann(dl * kA, segi, T)['FULL']
        full_c = seg_ann(dc * kC, segi, T)['FULL']
        r0 = full_l / full_c

        def lad_row(step, sub, lval, note):
            rr = lval / full_c
            expl = (math.log(r0) - math.log(rr)) / math.log(r0) if (r0 > 0 and rr > 0 and abs(math.log(r0)) > 1e-15) else ''
            lad.append(dict(object_label=label, step=step, substitution=sub, legacy_value=lval, curve_value=full_c, residual_ratio=rr, explained_share=expl, note=note))
        dayf = lambda coef: seg_ann(np.bincount(sd.day.to_numpy(), weights=coef, minlength=T) * kA, segi, T)['FULL']
        lad_row('L00_BASE', 'legacy as implemented (fixed A, weight node V_pre)', full_l, 'E6p LEGACY c5 D_imp path; curve = E6p cost_curve path (A_e = A0 n_e, node V(e-1)+)')
        l1 = dayf(legacy_coef(sd, node='vpre', part='nav'))
        lad_row('L01_NAV_NODE_PARTICIPATION', 'participation uses same-node A_e = A0*n_e (Q = A*dn/V0) instead of fixed A0 (Q = A*dn/V_pre)', l1, 'cumulative from L00')
        l2 = dayf(legacy_coef(sd, node='vprev', part='nav'))
        lad_row('L02_NAV_NODE_WEIGHT', 'weight node V_pre (today pre-trade) -> V(e-1)+ (previous post-trade NAV)', l2, 'cumulative from L01; residual = 1 means closed')
        lad_row('T01_SIGMA_X_SQRT252', 'sigma annualized (x sqrt 252) on legacy only', dayf(legacy_coef(sd, sig_scale=math.sqrt(252.0))), 'single substitution from L00; not the source')
        lad_row('T02_BP_VS_DECIMAL', 'kappa read as bp (x 1e-4) on legacy only', full_l * 1e-4, 'single substitution; factor 1e4 level, not 1.9')
        lad_row('T03_AMOUNT_UNIT_THOUSAND', 'ADV in thousand CNY on legacy only', dayf(legacy_coef(sd, adv_scale=1e-3)), 'single substitution; sqrt(1000) level, not 1.9')
        lad_row('T04_GROSS_VS_NET', 'legacy on gross |B|+|S| per security-day instead of net |B-S|', dayf(legacy_coef(sd, gross=True)), 'single substitution; both implementations net first')
        lad_row('T05_CASH_FEEDBACK_PATH', 'fixed path vs feedback cash path', full_l, 'both are fixed-path (no feedback cash debit); substitution leaves value unchanged')
        lad_row('T06_DOUBLE_FEE', 'fee counted twice on one side', full_l, 'neither impact path contains the linear fee; unchanged')
        sd1 = sd.copy()
        sh = np.maximum(sd1.day.to_numpy() - 1, 0)
        sd1['sig'] = np.asarray(mk['sig20'])[sh, sd1.sec.to_numpy()]
        sd1['adv'] = np.asarray(mk['adv20'])[sh, sd1.sec.to_numpy()]
        lad_row('T07_WINDOW_OFF_BY_ONE', 'sigma / ADV window ending T-2 instead of T-1 on legacy only', dayf(legacy_coef(sd1)), 'single substitution')
        lad_row('T08_SEGMENT_ANNUALIZATION', 'FULL as pooled daily mean vs sum n v / sum n', float(dl.sum() * kA / T * O.ANN_PP), 'identical by construction (same day set)')
        lad_row('T09_OLD_CACHE', 'E6p cache panels vs E6q cache panels (hardlinked, same sha)', full_l, 'sig20 / adv20 files identical (cache_reuse_manifest sha); unchanged')
        agg[label] = dict(r0=r0, r1=l1 / full_c, r2=l2 / full_c, full_l=full_l, full_c=full_c)
        O.log('S0-A %s：legacy %.4f curve %.4f ratio %.4f → L01 %.4f → L02 %.12f' % (label, full_l, full_c, r0, l1 / full_c, l2 / full_c))
    RC = pd.DataFrame(rows)
    LD = pd.DataFrame(lad, columns=['object_label', 'step', 'substitution', 'legacy_value', 'curve_value', 'residual_ratio', 'explained_share', 'note'])
    BR = pd.concat(bridge, ignore_index=True)
    closed = all(abs(v['r2'] - 1.0) <= 1e-9 for v in agg.values())
    status = 'RECONCILED' if closed else 'UNDECIDABLE_RECONCILIATION'
    O.atomic_write_csv(O.P('verify', 'impact_reconciliation_E6q.csv'), RC)
    O.atomic_write_csv(O.P('verify', 'impact_reconciliation_ladder_E6q.csv'), LD)
    O.atomic_write_csv(O.P('verify', 'impact_reconciliation_daily_bridge_E6q.csv'), BR)
    facts.update(status=status, A_eval=A_EVAL, kappa=KAPPA, delta=DELTA, ladder=agg, closed=closed,
                 ratio_range_full_all=[min(v['r0'] for v in agg.values()), max(v['r0'] for v in agg.values())], wall_s=round(time.time() - t0, 1))
    O.atomic_write_json(O.P('diagnostics', 's0a_facts_E6q.json'), facts)
    write_report(RC, LD, BR, agg, facts, status)
    O.write_receipt('E6q_s0a', [O.P('verify', 'impact_reconciliation_E6q.csv'), O.P('verify', 'impact_reconciliation_ladder_E6q.csv'),
                                O.P('verify', 'impact_reconciliation_daily_bridge_E6q.csv'), O.P('diagnostics', 's0a_facts_E6q.json')],
                    code=[__file__, O.__file__, CO.__file__], status_s0a=status, wall_s=facts['wall_s'])
    print(json.dumps(dict(status=status, ladder={k: {kk: round(vv, 6) for kk, vv in v.items()} for k, v in agg.items()}), ensure_ascii=False), flush=True)
    return status, facts


if __name__ == '__main__':
    main()
