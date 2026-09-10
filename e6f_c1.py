#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6f 块 C1: 画像 + 规模冲击成本 (§6.1)。一个进程 = 一个段。
   覆盖 U0-broad (重建 E6e 全部配置并逐个对已存日账本验证) ∪ UA (块 A 描述符)。
   用法: python e6f_c1.py --out DIR --period P
"""
import os, sys, json, time, argparse, traceback, collections
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as BA

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--period', required=True)
ap.add_argument('--limit', type=int, default=0)
ap.add_argument('--horizon_only', action='store_true',
                help='只给 A_horizon 的 12 锚 × 7 个 H 出括号与情景 (Q6 需要冲击后的 H 曲线); '
                     '跳过 E6e 重建与 UA 全量, 产物另存 *_H_<段>.*')
A = ap.parse_args()
PN = A.period
for d in ('C_exposures', 'C_orders', 'C_impact', 'C_capacity_scenarios', 'checks',
          'logs', 'task_status'):
    os.makedirs(os.path.join(A.out, d), exist_ok=True)
_TAG = ('c1h_%s' if A.horizon_only else 'c1_%s') % PN   # 别把正在跑的主 C1 日志截断
_lf = open(os.path.join(A.out, 'logs', '%s.log' % _TAG), 'w', encoding='utf-8', buffering=1)


def P(s=''):
    print(s, flush=True); _lf.write(s + '\n')


T0 = time.time()
AGRID = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0]      # 亿元
KGRID = [0.25, 0.5, 1.0]
YI = 1e8
P('=== C1 [%s] === %s' % (PN, time.strftime('%Y-%m-%d %H:%M:%S')))
S = F.build_segment(PN, 'legacy_all')
cc = S.ccols

# ============================================================
# 市场量 (执行日 e 的输入截止 e-1)
# ============================================================
amt = S.data['amount'].astype(float)
isop = (S.data.get('is_open') == 1)
amt_open = amt.where(isop)
ADV20 = amt_open.rolling(20, min_periods=10).mean().shift(1).values[:, cc]      # 主口径: 交易日
ADV20c = amt.rolling(20, min_periods=10).mean().shift(1).values[:, cc]          # 敏感性: 含停牌 0
ADV60 = amt_open.rolling(60, min_periods=30).mean().shift(1).values[:, cc]
SIG20 = S.dr.rolling(20, min_periods=10).std().shift(1).values[:, cc]
SIG60 = S.dr.rolling(60, min_periods=30).std().shift(1).values[:, cc]
MCAP = S.data.get('mcap').astype(float).values[:, cc]
AMT_E = amt.values[:, cc]                                                       # 执行日实得成交额
OPEN_E = isop.values[:, cc]
FLAGB = (S.data['flag_buy'].values[:, cc] if 'flag_buy' in S.data else None)
FLAGS_ = (S.data['flag_sell'].values[:, cc] if 'flag_sell' in S.data else None)
FLAGST = (S.data['flag_st'].values[:, cc] if 'flag_st' in S.data else None)
IC = S.icodes
P('  ADV20(交易日) 非缺率 %.3f; ADV20(含停牌0) 非缺率 %.3f; sigma20 非缺率 %.3f'
  % (np.mean(~np.isnan(ADV20)), np.mean(~np.isnan(ADV20c)), np.mean(~np.isnan(SIG20))))
adv_pct = pd.DataFrame(ADV20).rank(axis=1, pct=True).values                     # 全市场(候选列)分位
mc_pct = pd.DataFrame(MCAP).rank(axis=1, pct=True).values
LOWADV = adv_pct < 0.20


def walk_holdings(idx, val, H=K.HOLD, tol=1e-15):
    """增量走一遍 ah_t 与 q_t = ah_t - ah_{t-1}。
       ah_t = (Σ_{s=t-1-H}^{t-2} W[s]) / den[t-2] —— 与 sparse_pnl_H 的窗口逐字相同。
       每天两个 O(Nc) 向量操作, 不用 Python 字典 (字典版按 6,038 配置会慢到不可用)。"""
    T, Nc = S.T, S.Nc
    den = np.minimum(np.arange(1, T + 1), H).astype(float)
    cur = np.zeros(Nc)
    prev = np.zeros(Nc)
    for t in range(2, T):
        sa, sr = t - 2, t - 2 - H
        if len(idx[sa]):
            cur[idx[sa]] += val[sa]
        if sr >= 0 and len(idx[sr]):
            cur[idx[sr]] -= val[sr]
        ah = cur / den[t - 2]
        q = ah - prev
        hz = np.flatnonzero(np.abs(ah) > tol)
        qz = np.flatnonzero(np.abs(q) > tol)
        yield t, hz, ah[hz], qz, q[qz]
        prev = ah


def profile_and_impact(idx, val, H=K.HOLD):
    """返回 (brackets dict, 画像聚合 dict, 逐日 Σ|q|)。四个 bracket 都与 (A, κ) 无关:
       sqrt : Σ|q|^1.5 σ20/√ADV20   -> c = κ·√A · bracket        (平方根律, 主口径)
       cal  : 同上但 ADV 含停牌 0                                   (敏感性)
       s60  : Σ|q|^1.5 σ60/√ADV60                                (窗口敏感性)
       lin  : Σ q²σ20/ADV20         -> c = (κA/√p0)·bracket, p0=1% (线性形式敏感性 §6.1)"""
    T = S.T
    br = np.full(T, np.nan); brc = np.full(T, np.nan)
    br60 = np.full(T, np.nan); brl = np.full(T, np.nan)
    tw = np.zeros(T); qmiss = np.zeros(T)
    acc = collections.defaultdict(list)
    n_ord = 0
    for t, hz, w, qz, q in walk_holdings(idx, val, H):
        if len(qz):
            n_ord += 1
            aq = np.abs(q)
            tw[t] = aq.sum()
            s_, a_, ac_ = SIG20[t, qz], ADV20[t, qz], ADV20c[t, qz]
            s6_, a6_ = SIG60[t, qz], ADV60[t, qz]
            ok = ~np.isnan(s_) & ~np.isnan(a_) & (a_ > 0)
            okc = ~np.isnan(s_) & ~np.isnan(ac_) & (ac_ > 0)
            ok6 = ~np.isnan(s6_) & ~np.isnan(a6_) & (a6_ > 0)
            qmiss[t] = float(aq[~ok].sum())
            if ok.any():
                br[t] = float(np.sum(aq[ok] ** 1.5 * s_[ok] / np.sqrt(a_[ok])))
                brl[t] = float(np.sum(aq[ok] ** 2 * s_[ok] / a_[ok]))
            if okc.any():
                brc[t] = float(np.sum(aq[okc] ** 1.5 * s_[okc] / np.sqrt(ac_[okc])))
            if ok6.any():
                br60[t] = float(np.sum(aq[ok6] ** 1.5 * s6_[ok6] / np.sqrt(a6_[ok6])))
            wq = aq / aq.sum()
            acc["tw_mc_pct"].append(float(np.nansum(wq * mc_pct[t, qz])))
            acc["tw_adv_pct"].append(float(np.nansum(wq * adv_pct[t, qz])))
            acc["tw_lowadv"].append(float(wq[LOWADV[t, qz]].sum()))
            if FLAGST is not None:
                acc["tw_st"].append(float(np.nansum(wq * (FLAGST[t, qz] == 1))))
            if FLAGB is not None:
                acc["tw_nobuy"].append(float(np.nansum(wq * (FLAGB[t, qz] == 0))))
            if FLAGS_ is not None:
                acc["tw_nosell"].append(float(np.nansum(wq * (FLAGS_[t, qz] == 0))))
            with np.errstate(invalid="ignore", divide="ignore"):
                pr = AMT_E[t, qz] / ADV20[t, qz]        # 执行日实得成交额 / ADV20 压力比
            acc["pressure"].append(float(np.nansum(wq * pr)))
        if not len(hz):
            continue
        tot = w.sum()
        if tot <= 0:
            continue
        p_ = w / tot
        acc["names"].append(len(hz))
        acc["hhi"].append(float((p_ ** 2).sum()))
        acc["effN"].append(float(1.0 / (p_ ** 2).sum()))
        acc["wmax"].append(float(w.max()))
        acc["invested"].append(float(tot))
        ic = IC[t, hz]
        v = ic >= 0
        if v.any():
            gs = np.bincount(ic[v], weights=w[v], minlength=S.G)
            acc["ind_top"].append(float(gs.max()))
            acc["ind_cap_hit"].append(float((gs > S.cap[t] - 1e-12).sum()))
        acc["mc_med_pct"].append(float(np.nanmedian(mc_pct[t, hz])))
        acc["adv_med_pct"].append(float(np.nanmedian(adv_pct[t, hz])))
        acc["w_lowadv"].append(float(w[LOWADV[t, hz]].sum()))
        acc["w_susp"].append(float(w[~OPEN_E[t, hz]].sum()))
        if FLAGST is not None:
            acc["w_st"].append(float(np.nansum(w * (FLAGST[t, hz] == 1))))
            acc["w_unknown_flag"].append(float(np.nansum(w * np.isnan(FLAGST[t, hz]))))
        if FLAGB is not None:
            acc["w_nobuy"].append(float(np.nansum(w * (FLAGB[t, hz] == 0))))
        if FLAGS_ is not None:
            acc["w_nosell"].append(float(np.nansum(w * (FLAGS_[t, hz] == 0))))
    prof = {k: (float(np.nanmean(v)) if len(v) else np.nan) for k, v in acc.items()}
    prof["q_missing_share"] = float(np.nansum(qmiss) / max(np.nansum(tw), 1e-12))
    prof["n_order_days"] = n_ord
    return dict(sqrt=br, cal=brc, s60=br60, lin=brl), prof, tw


# ============================================================
# 配置来源: E6e 全量重建 + UA
# ============================================================
DOM = set(pd.read_csv(os.path.join(A.out, 'domain_U0.csv')).config_id)
GG = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_gross_%s.parquet' % PN))
TT = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_turn_%s.parquet' % PN))
PPz = pd.read_parquet(os.path.join(F.E6E_DIR, 'daily', 'daily_pos_%s.parquet' % PN))

BRS, PROF, VERIF = {}, {}, []
TASK = F.TaskTable(os.path.join(A.out, 'task_status', '%s.csv' % _TAG))


def handle(cid, idx, val, src, H=K.HOLD, meta=None):
    brs, prof, tw = profile_and_impact(idx, val, H)
    for kk, vv in brs.items():
        BRS.setdefault(kk, {})[cid] = vv
    d = dict(config_id=cid, period=PN, source=src, H=H)
    d.update(prof)
    if meta:
        d.update(meta)
    PROF[cid] = d
    if cid in GG.columns:
        g, p, u, _ = F.sparse_pnl_H(S, idx, val, H)
        m = ~np.isnan(g) & ~np.isnan(GG[cid].values)
        VERIF.append(dict(config_id=cid, d_gross=float(np.max(np.abs(g[m] - GG[cid].values[m]))),
                          d_turn=float(np.max(np.abs(u - TT[cid].values))),
                          d_pos=float(np.max(np.abs(p - PPz[cid].values)))))
        d['sum_absq_over_2turn'] = float(np.nansum(tw) / max(2 * np.nansum(u), 1e-12))
    return d


# ============================================================
# --horizon_only: A_horizon 的冲击后 H 曲线 (Q6)
#   块 A 只给 H 分支出了 net/turn/pos, 没有括号 —— 而 H 越短换手越高, 冲击成本按
#   Σ|q|^1.5 走, 不能用"换手比的 1.5 次方"糊过去。这里对同一组权重逐 H 真算一遍。
# ============================================================
if A.horizon_only:
    P('')
    P('=== A_horizon 冲击后 H 曲线 (只跑 12 锚 × 7 个 H) ===')
    ctxh = BA.Ctx(S)
    CFH = {c['config_id']: c for c in D.gen_all()}
    # A_horizon 只含 H≠5 的 6 个格位; H5 那一格按 parent_id 回捞 ——
    # 12 个锚里有 3 个 (无否决的) 的 H5 格位被去重进了 P54_default, 只认 A12_anchor 会漏掉。
    hz_ = [c for c in CFH.values() if c['layer'] == 'A_horizon']
    par_ = {c['parent_id'] for c in hz_ if c.get('parent_id') in CFH}
    anch_ = {}
    for c in hz_:
        if c.get('parent_id'):
            anch_[c['parent_id']] = c.get('anchor')
    hcf = hz_ + [dict(CFH[p], anchor=anch_.get(p)) for p in sorted(par_)]
    assert len(hcf) == 84, '锚 × H 格位数 %d ≠ 84' % len(hcf)
    t1 = time.time()
    nh = 0
    for c in sorted(hcf, key=lambda x: (str(x.get('anchor')), x['H'])):
        cid = c['config_id']
        try:
            mk = ctxh.full_mask(c)[0]
            iv = F.dev_from_dense(S, mk)
            d = handle(cid, iv[0], iv[1], 'A_horizon', H=int(c['H']),
                       meta=dict(anchor=c.get('anchor'), layer=c['layer']))
            nh += 1
        except Exception as e:
            P('  !! %s -> %s' % (cid, str(e)[:120]))
    P('  完成 %d 个 %.0fs' % (nh, time.time() - t1))
    colsH = sorted(BRS['sqrt'])
    for kk in ('sqrt', 'cal', 's60', 'lin'):
        np.save(os.path.join(A.out, 'C_impact',
                             'bracket%s_H_%s.npy' % ('' if kk == 'sqrt' else '_' + kk, PN)),
                np.column_stack([BRS[kk][c] for c in colsH]))
    json.dump(colsH, open(os.path.join(A.out, 'C_impact',
                                       'bracket_cols_H_%s.json' % PN), 'w'))
    pd.DataFrame(PROF).T.to_csv(os.path.join(A.out, 'C_exposures',
                                             'profile_H_%s.csv' % PN))
    # 冲击后 net: net8 日序列取自块 A 的 H 分支日账本
    AG = pd.read_parquet(os.path.join(A.out, 'daily', 'A_gross_%s__legacy_all.parquet' % PN))
    AT = pd.read_parquet(os.path.join(A.out, 'daily', 'A_turn_%s__legacy_all.parquet' % PN))
    rowsH = []
    BR_H = {k: np.column_stack([BRS[k][c] for c in colsH]) for k in ('sqrt', 'cal', 's60', 'lin')}
    have = [c for c in colsH if c in AG.columns]
    jh = [colsH.index(c) for c in have]
    N8H = np.column_stack([AG[c].values - AT[c].values * (F.COST / 1e4) for c in have])
    P0h = 0.01
    FORMSH = {'sqrt': lambda Ay, kp: kp * np.sqrt(Ay * YI),
              'cal': lambda Ay, kp: kp * np.sqrt(Ay * YI),
              's60': lambda Ay, kp: kp * np.sqrt(Ay * YI),
              'lin': lambda Ay, kp: kp * (Ay * YI) / np.sqrt(P0h)}
    for form, fn in FORMSH.items():
        Bm = BR_H[form][:, jh]
        for Ay in AGRID:
            for kp in KGRID:
                C_ = Bm * fn(Ay, kp)
                NI = N8H - C_
                m = ~np.isnan(NI)
                with np.errstate(invalid='ignore'):
                    ca = 252 * 100 * np.nansum(np.where(m, C_, 0.0), axis=0) / np.maximum(m.sum(0), 1)
                    na = 252 * 100 * np.nansum(np.where(m, NI, 0.0), axis=0) / np.maximum(m.sum(0), 1)
                rowsH.append(pd.DataFrame(dict(
                    config_id=have, period=PN, form=form, A_yi=Ay, kappa=kp,
                    H=[int(CFH[c]['H']) for c in have],
                    anchor=[CFH[c].get('anchor') for c in have],
                    cost_impact_ann=ca, net_impact_ann=na, n_days=m.sum(0))))
    IMH = pd.concat(rowsH, ignore_index=True)
    IMH.to_csv(os.path.join(A.out, 'C_impact', 'impact_scenarios_H_%s.csv' % PN), index=False)
    P('  情景行 %d (%d 格位 × %d A × %d κ × 4 形式)'
      % (len(IMH), len(have), len(AGRID), len(KGRID)))
    sq = IMH[(IMH.form == 'sqrt') & (IMH.kappa == 0.5)]
    P('  [平方根 κ=0.5] 冲击后 net 中位, 行=H 列=A(亿):')
    P(sq.pivot_table(index='H', columns='A_yi', values='net_impact_ann',
                     aggfunc='median').round(2).to_string())
    json.dump(dict(period=PN, mode='horizon_only', n=nh, n_scen=len(IMH),
                   seconds=time.time() - T0),
              open(os.path.join(A.out, 'checks', 'c1h_%s.json' % PN), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    P('')
    P('C1 [%s] horizon_only 完成 %.0fs' % (PN, time.time() - T0))
    _lf.close()
    sys.exit(0)

P('')
P('=== 重建 E6e U0-broad 配置 ===')
Sre = K.load_segment(PN, verbose=False)
CD = K.core_descriptors() + K.twin_descriptors(K.core_descriptors())
CM, CS_, CIV = {}, {}, {}
n = 0
t1 = time.time()
for d in CD:
    cid = d['core_id']
    try:
        m, sc, pool = K.build_core(Sre, d)
        mc = K.toc(Sre, m)
        if cid in CM:
            continue
        CM[cid] = mc; CS_[cid] = sc
        CIV[cid] = K.dev_from_mask(Sre, mc)
        if cid in DOM:
            handle(cid, CIV[cid][0], CIV[cid][1], 'E6e_core', meta=dict(kind='core'))
            n += 1
    except Exception as e:
        TASK.reg(cid, 'c1_core'); TASK.set(cid, 'FAILED', note=str(e)[:150])
P('  核 %d 个 (进 C1 的 %d) %.0fs' % (len(CM), n, time.time() - t1))

P('  否决族...')
t1 = time.time()
tox = {k: K.toc(Sre, v) for k, v in K.tox_masks(Sre).items()}
full_tox = K.tox_masks(Sre)
unsc = {f: K.toc(Sre, K.unscorable_mask(Sre, f)) for f in K.VF6}
EXTREME = K.extreme_masks(Sre)
COLPOS = K.col_positions(Sre)
P54 = [d['core_id'] for d in K.core_descriptors() if d['set'] == 'P54']
hard = K.hard_veto_descriptors()
comp = K.composite_veto_descriptors()
exem = K.exemption_veto_descriptors()
soft = K.soft_descriptors()
nv = 0
for cid in ([d['core_id'] for d in CD] if False else sorted(CM)):
    base = CM[cid]
    for vd in hard:
        cid2 = '%s|%s' % (cid, vd['veto_id'])
        if cid2 not in DOM:
            continue
        dr = np.zeros_like(base)
        for (f, k) in vd['legs']:
            dr |= tox[(f, k)]
        iv = K.dev_from_mask(Sre, base & ~dr)
        handle(cid2, iv[0], iv[1], 'E6e_hard', meta=dict(kind='hard', core=cid, veto=vd['veto_id']))
        nv += 1
    if cid not in P54:
        continue
    fullbase = np.zeros((Sre.T, Sre.Nfull), bool)
    fullbase[:, Sre.ccols] = base
    for vd in comp + exem:
        cid2 = '%s|%s' % (cid, vd['veto_id'])
        if cid2 not in DOM:
            continue
        drop_full, _ = K.veto_drop(Sre, vd, full_tox, unsc, core_mask=fullbase,
                                   core_score=CS_[cid], cand_pool=None,
                                   extreme=EXTREME, colpos=COLPOS)
        iv = K.dev_from_mask(Sre, base & ~K.toc(Sre, drop_full))
        handle(cid2, iv[0], iv[1], 'E6e_' + vd['kind'],
               meta=dict(kind=vd['kind'], core=cid, veto=vd['veto_id']))
        nv += 1
    pv = CIV[cid]
    for st in K.SOFT_STARTS:
        d0 = K.toc(Sre, K.parse_start(Sre, st, full_tox))
        inD = base & d0
        hv = K.dev_from_mask(Sre, base & ~d0)
        w0 = pv[1]
        for vd in [x for x in soft if x['start'] == st]:
            cid2 = '%s|%s' % (cid, vd['veto_id'])
            if cid2 not in DOM:
                continue
            lam = vd['lam']
            if vd['mode'] == 'WS':
                val = []
                for t in range(Sre.T):
                    v = w0[t].copy()
                    if len(v):
                        inm = inD[t][pv[0][t]]
                        v[inm] = v[inm] * (1.0 - lam)
                    val.append(v)
                iv = (pv[0], val)
            else:
                val, idx = [], []
                for t in range(Sre.T):
                    u = np.union1d(pv[0][t], hv[0][t])
                    a_ = np.zeros(len(u)); b_ = np.zeros(len(u))
                    if len(pv[0][t]):
                        a_[np.searchsorted(u, pv[0][t])] = w0[t]
                    if len(hv[0][t]):
                        b_[np.searchsorted(u, hv[0][t])] = hv[1][t]
                    v = (1 - lam) * a_ + lam * b_
                    nz = v != 0
                    idx.append(u[nz]); val.append(v[nz])
                iv = (idx, val)
            handle(cid2, iv[0], iv[1], 'E6e_soft',
                   meta=dict(kind='soft', core=cid, veto=vd['veto_id']))
            nv += 1
    if (nv % 2000) == 0 and nv:
        P('    否决族 %d 个, %.0fs' % (nv, time.time() - t1))
    if A.limit and (n + nv) > A.limit:
        break
P('  否决类 %d 个 %.0fs; C1 覆盖 E6e 配置合计 %d / U0-broad %d'
  % (nv, time.time() - t1, len(PROF), len(DOM)))

VF = pd.DataFrame(VERIF)
if len(VF):
    w = float(np.nanmax(VF[['d_gross', 'd_turn', 'd_pos']].values))
    P('  重建对 E6e 日账本: %d 个配置, max|d| = %.3e (阈 1e-12) %s'
      % (len(VF), w, 'OK' if w < 1e-12 else 'FAIL'))
    VF.to_csv(os.path.join(A.out, 'checks', 'c1_rebuild_verify_%s.csv' % PN), index=False)
    if 'sum_absq_over_2turn' in list(PROF.values())[0]:
        r = [d.get('sum_absq_over_2turn') for d in PROF.values() if d.get('sum_absq_over_2turn')]
        P('  订单恒等式 Σ|q| / (2·turn) : 中位 %.12f (应恒为 1)' % float(np.nanmedian(r)))

# ---- UA (块 A 描述符) ----
P('')
P('=== UA 配置 ===')
t1 = time.time()
CFGS = sorted([c for c in D.gen_all() if c['H'] == 5], key=lambda c: c['core_id'])
if A.limit:
    CFGS = CFGS[:A.limit]
ctx = BA.Ctx(S)
nu = 0
for c in CFGS:
    try:
        mk = ctx.full_mask(c)[0]
        idx, val = F.dev_from_dense(S, mk)
        handle('UA::' + c['config_id'], idx, val, 'UA', H=5,
               meta=dict(kind='UA', core=c['core_id'], veto=c['veto_id'], layer=c['layer']))
        nu += 1
    except Exception:
        pass
    if (nu % 500) == 0 and nu:
        P('    UA %d/%d %.0fs' % (nu, len(CFGS), time.time() - t1))
P('  UA %d 个 %.0fs' % (nu, time.time() - t1))

# ============================================================
# 情景表: 21 个 (A, κ) = bracket 的标量倍
# ============================================================
P('')
P('=== 冲击情景 (bracket 的标量倍) ===')
cols = sorted(BRS['sqrt'])
BRm = np.column_stack([BRS['sqrt'][c] for c in cols])
for kk in ('sqrt', 'cal', 's60', 'lin'):
    np.save(os.path.join(A.out, 'C_impact', 'bracket%s_%s.npy' % ('' if kk == 'sqrt' else '_' + kk, PN)),
            np.column_stack([BRS[kk][c] for c in cols]))
json.dump(cols, open(os.path.join(A.out, 'C_impact', 'bracket_cols_%s.json' % PN), 'w'))
pd.DataFrame(PROF).T.to_csv(os.path.join(A.out, 'C_exposures', 'profile_%s.csv' % PN))

net8 = {}
for c in cols:
    if c in GG.columns:
        net8[c] = GG[c].values - TT[c].values * (F.COST / 1e4)
BR_ALL = {k: np.column_stack([BRS[k][c] for c in cols]) for k in ('sqrt', 'cal', 's60', 'lin')}
P0 = 0.01                                    # 线性形式的参考参与率
FORMS = {'sqrt': lambda Ay, kp: kp * np.sqrt(Ay * YI),          # c = κ√A · bracket
         'cal': lambda Ay, kp: kp * np.sqrt(Ay * YI),
         's60': lambda Ay, kp: kp * np.sqrt(Ay * YI),
         'lin': lambda Ay, kp: kp * (Ay * YI) / np.sqrt(P0)}    # c = (κA/√p0) · bracket
rows = []
jsel = [j for j, c in enumerate(cols) if c in net8]
csel = [cols[j] for j in jsel]
N8m = np.column_stack([net8[c] for c in csel])
for form, sc_fn in FORMS.items():
    Bm = BR_ALL[form][:, jsel]
    for Ay in AGRID:
        for kp in KGRID:
            C_ = Bm * sc_fn(Ay, kp)
            NI = N8m - C_
            m = ~np.isnan(NI)
            with np.errstate(invalid='ignore'):
                ca = 252 * 100 * np.nansum(np.where(m, C_, 0.0), axis=0) / np.maximum(m.sum(0), 1)
                na = 252 * 100 * np.nansum(np.where(m, NI, 0.0), axis=0) / np.maximum(m.sum(0), 1)
            rows.append(pd.DataFrame(dict(config_id=csel, period=PN, form=form,
                                          A_yi=Ay, kappa=kp, cost_impact_ann=ca,
                                          net_impact_ann=na, n_days=m.sum(0))))
IMP = pd.concat(rows, ignore_index=True)
IMP.to_csv(os.path.join(A.out, 'C_impact', 'impact_scenarios_%s.csv' % PN), index=False)
P('  情景行 %d (%d 配置 × %d A × %d κ × %d 形式: 平方根/含停牌0/60日窗/线性)'
  % (len(IMP), len(csel), len(AGRID), len(KGRID), len(FORMS)))

# 容量情景 (§6.1): 平方根律下净超额降至 0 与相对 R1/R2 增量降至 0 的 A
P('')
P('=== 容量情景 ===')
b0 = IMP[(IMP.form == 'sqrt') & (IMP.A_yi == 1.0) & (IMP.kappa == 0.5)].set_index('config_id')
base_net = {c: 252 * 100 * float(np.nanmean(net8[c])) for c in csel}
cap = []
for c in csel:
    if c not in b0.index:
        continue
    c1 = float(b0.loc[c, 'cost_impact_ann'])          # A=1亿, κ=0.5 时的冲击成本
    n0 = base_net[c]
    # c(A) = c1·√A  ->  n0 - c1√A = 0  ->  A* = (n0/c1)²
    a_zero = (n0 / c1) ** 2 if (c1 > 0 and n0 > 0) else np.nan
    a_half = (0.5 * n0 / c1) ** 2 if (c1 > 0 and n0 > 0) else np.nan
    row = dict(config_id=c, period=PN, net8_ann=n0, cost_at_1yi_k05=c1,
               A_star_net_zero_yi=a_zero, A_star_half_gross_yi=a_half,
               extrapolated_beyond_grid=bool(a_zero == a_zero and a_zero > max(AGRID)),
               sign_case=('net<=0' if n0 <= 0 else ('cost<=0' if c1 <= 0 else 'ok')))
    for ref, rc in (('R1', 'KT_dep(50,50)|C:k5'), ('R2', 'KT_mean@30|C:k5+cr5:k10')):
        if rc in base_net and rc in b0.index:
            d0 = n0 - base_net[rc]
            db = c1 - float(b0.loc[rc, 'cost_impact_ann'])
            # d(A) = d0 - db·√A = 0 -> A* = (d0/db)²; db<=0 表示成本更低, 增量不会因规模消失
            row['A_star_vs_%s_yi' % ref] = ((d0 / db) ** 2 if (db > 0 and d0 > 0) else np.nan)
            row['d_vs_%s_ann' % ref] = d0
            row['sign_case_%s' % ref] = ('d<=0' if d0 <= 0 else ('db<=0(不消失)' if db <= 0 else 'ok'))
    cap.append(row)
CAP = pd.DataFrame(cap)
CAP.to_csv(os.path.join(A.out, 'C_capacity_scenarios', 'capacity_%s.csv' % PN), index=False)
P('  容量表 %d 行; 净超额降至 0 的 A 中位 %.1f 亿 (超出扫描上限 %d亿 的占 %.1f%%)'
  % (len(CAP), CAP.A_star_net_zero_yi.median(), int(max(AGRID)),
     100 * CAP.extrapolated_beyond_grid.mean()))

json.dump(dict(period=PN, n_profiles=len(PROF), n_e6e=len(VF), n_ua=nu,
               rebuild_max_abs_diff=(float(np.nanmax(VF[['d_gross', 'd_turn', 'd_pos']].values))
                                     if len(VF) else None),
               A_grid=AGRID, kappa_grid=KGRID, seconds=time.time() - T0),
          open(os.path.join(A.out, 'checks', 'c1_%s.json' % PN), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
P('')
P('C1 [%s] 完成 %.0fs' % (PN, time.time() - T0))
_lf.close()
open(os.path.join(A.out, 'task_status', '_DONE_C1_%s' % PN), 'w').write(
    '%s n_profiles=%d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), len(PROF)))
