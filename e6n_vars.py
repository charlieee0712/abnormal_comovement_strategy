# -*- coding: utf-8 -*-
"""E6n 测量输入变体（plan §6.2 生成语法、§6.4 / §6.4a 对照；brief §1.3-5 / -7）。不读收益。
变体字符串（registry/input_variants_E6n.csv）→ 单元向量：
  FACET|f|eta|app|f<fr>|d±1   五面 / OHLC 桥：q_refined = where(激活, (1−η)·kQ + η·k_m, kQ)；激活 = 作用域（QGOOD / ALL）∧ k_m 有限 ∧ kQ 有限
  RAW|F|lam|app|f<fr>|sup:fam raw 构造与控制：完整参考域 Q0 原值，只对激活股票写 1/(d + λh + ε)，走源 Q 同一中性化 / 'lo' 排名，
                              再把非激活覆盖回 kQ；λ = 0 或整日无激活 → 当日 kQ（逐位）；激活 = 作用域 ∧ 支持族有效掩码 ∧ h 有限非负 ∧ d / kQ / Q0 原值有限
  CLONE|f|eta|app|f<fr>       五面 MASK_CLONE：owner 有限域内按源过程重建 Q 秩 k_clone，再按 owner 激活集混合
  CLONE_RAW                   raw 类 MASK_CLONE：以 Q0 原值替换全部新 raw → 预期逐位回源 kQ（build 时实核并登记）
  DOSE|<owner 变体> / CDOSE|<owner 变体>：在名单层按母体旧 K 现算（dose_K / cdose_K）。
  build --seg S：预算 RAW / CLONE / CLONE_RAW 的单元向量 → meas/<段>/kf/<文件名>.npy + kf_manifest.csv（含激活数、激活日数、相对 kQ 改变数）。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6n_core as N

EPS = 1e-4
FACETS = ('PL_REL20', 'TAIL_PUSH', 'TAIL_VOL_REL20', 'JSD_PROFILE20', 'RV_REL20')
BRIDGES = ('K_RANGE_SOURCE', 'CLV20_SOURCE')


def fname(variant):
    return variant.replace('|', '__').replace(':', '-') + '.npy'


class Base(object):
    """一段的测量基表（meas/<段>/*.npy，单元向量）。"""

    def __init__(self, seg):
        self.seg = seg
        self.d = N.P('meas', seg)
        self._c = {}
        self.t = self.get('cells_t')
        self.c = self.get('cells_c')
        self.n = len(self.t)
        self.kQ = self.get('kQ')
        self.qgood = self.get('QGOOD').astype(bool)
        self.dd = self.get('d')
        self.q0raw = self.get('q0raw')

    def get(self, name):
        if name not in self._c:
            self._c[name] = np.load(os.path.join(self.d, name + '.npy'), allow_pickle=False)
        return self._c[name]

    def kf_cached(self, variant):
        return np.load(os.path.join(self.d, 'kf', fname(variant)), allow_pickle=False)

    def active_dom(self, app):
        return np.ones(self.n, bool) if app == 'ALL' else self.qgood.copy()


def parse(variant):
    p = variant.split('|')
    out = dict(family=p[0])
    if p[0] in ('FACET', 'CLONE'):
        out.update(feature=p[1], eta=float(p[2][3:]), app=p[3], fr=int(p[4][1:]), dir=(int(p[5][1:]) if len(p) > 5 else 1))
    elif p[0] == 'RAW':
        out.update(feature=p[1], lam=float(p[2][3:]), app=p[3], fr=int(p[4][1:]), sup=p[5][4:])
    elif p[0] in ('DOSE', 'CDOSE'):
        out.update(owner='|'.join(p[1:]))
    return out


def km_name(feature, fr, d):
    if feature in BRIDGES:
        return 'km_%s_f5_hi' % feature
    return 'km_%s_f%d_%s' % (feature, fr, 'hi' if d > 0 else 'lo')


def facet(B, variant):
    v = parse(variant)
    km = B.get(km_name(v['feature'], v['fr'], v['dir']))
    act = B.active_dom(v['app']) & np.isfinite(km) & np.isfinite(B.kQ)
    if v['eta'] == 0.0:
        return B.kQ.copy(), act
    kf = np.where(act, (1.0 - v['eta']) * B.kQ + v['eta'] * km, B.kQ)
    return kf, act


def raw_h(B, F, fr):
    if F == 'Q_PATH':
        return B.get('comp_h_path_f%d' % fr)
    if F == 'Q_RV':
        return B.get('comp_sqrtRV_f%d' % fr)
    if F == 'Q_RANGE':
        return B.get('comp_log_hl_f5')
    if F == 'Q_CLOSE_THIN':
        return B.get('comp_h_close_f5')
    if F == 'Q_CLOSE_LEVEL':
        return B.get('comp_h_close_level_f5')
    if F == 'Q_BOTH':
        return (B.get('comp_h_path_f5') + B.get('comp_h_close_f5')) / 2.0
    raise ValueError(F)


def support_mask(B, fam, fr):
    if fam == 'Q_PATH':
        return np.isfinite(B.get('comp_h_path_f%d' % fr))
    if fam == 'Q_CLOSE_THIN':
        return np.isfinite(B.get('comp_h_close_f5'))
    if fam == 'Q_BOTH':
        return np.isfinite(B.get('comp_h_path_f5')) & np.isfinite(B.get('comp_h_close_f5'))
    raise ValueError(fam)


def raw_active(B, variant):
    v = parse(variant)
    h = raw_h(B, v['feature'], v['fr'])
    act = (B.active_dom(v['app']) & support_mask(B, v['sup'], v['fr']) & np.isfinite(h) & (np.nan_to_num(h, nan=-1.0) >= 0)
           & np.isfinite(B.dd) & np.isfinite(B.kQ) & np.isfinite(B.q0raw))
    return act, h, v


def raw_kf(B, S, variant):
    act, h, v = raw_active(B, variant)
    lam = v['lam']
    if lam == 0.0 or not act.any():
        return B.kQ.copy(), act, dict(neutralized=False)
    raw = B.q0raw.copy()
    raw[act] = 1.0 / (B.dd[act] + lam * h[act] + EPS)
    G = np.full((S.T, S.Nc), np.nan)
    G[B.t, B.c] = raw
    kn = S.pct_cells(G, 'lo')
    kf = np.where(act, kn, B.kQ)
    days_act = np.unique(B.t[act])
    return kf, act, dict(neutralized=True, active_days=int(len(days_act)), kn_nan_on_active=int((~np.isfinite(kn[act])).sum()))


def clone_kf(B, S, variant):
    v = parse(variant)
    km = B.get(km_name(v['feature'], v['fr'], 1))
    dom = np.isfinite(km)
    G = np.full((S.T, S.Nc), np.nan)
    G[B.t, B.c] = B.q0raw
    kcl = S.pct_cells(G, 'lo', pool=S.pool_of_cells(dom))
    act = B.active_dom(v['app']) & dom & np.isfinite(B.kQ)
    kf = np.where(act, (1.0 - v['eta']) * B.kQ + v['eta'] * kcl, B.kQ)
    return kf, act, dict(clone_vs_kQ_cells_differ=int((np.isfinite(kcl) & (kcl != B.kQ)).sum()), clone_domain=int(dom.sum()))


def clone_raw(B, S):
    G = np.full((S.T, S.Nc), np.nan)
    G[B.t, B.c] = B.q0raw
    kn = S.pct_cells(G, 'lo')
    same = (np.isfinite(kn) == np.isfinite(B.kQ)).all() and bool((kn[np.isfinite(kn)] == B.kQ[np.isfinite(B.kQ)]).all())
    return kn, dict(bitwise_equal_kQ=bool(same), finite=int(np.isfinite(kn).sum()))


def variant_kf(B, variant):
    """名单层取 kf：FACET 现算；RAW / CLONE / CLONE_RAW 读缓存；Q0 = kQ。"""
    f = variant.split('|')[0]
    if variant == 'Q0':
        return B.kQ, np.zeros(B.n, bool)
    if f == 'FACET':
        return facet(B, variant)
    if f in ('RAW', 'CLONE', 'CLONE_RAW'):
        kf = B.kf_cached(variant)
        act = (raw_active(B, variant)[0] if f == 'RAW' else
               (facet(B, 'FACET|' + '|'.join(variant.split('|')[1:]) + '|d+1')[1] if f == 'CLONE' else np.zeros(B.n, bool)))
        return kf, act
    raise ValueError(variant)


# ------------------------------------------------------------------ DOSE / COMPONENT_DOSE（名单层现算；附录 dose_match 同式）
def dose_match(base_delta, target_delta):
    b = np.asarray(base_delta, float)
    d = np.asarray(target_delta, float)
    if b.size == 0:
        return None
    sb = float(b.std())
    sd = float(d.std())
    tol = 64 * np.finfo(float).eps * max(1., float(np.abs(b).max(initial=0)), float(np.abs(d).max(initial=0)))
    if sb <= tol and sd > tol:
        return None
    if sb <= tol:
        return np.full(b.shape, d.mean())
    return d.mean() + sd / sb * (b - b.mean())


def native_q(k0, kf, a):
    a = float(a)
    return np.where(np.isfinite(kf), (1 - a) * k0 + a * kf, k0)


def dose_K(k0, kQ, kf_owner, act, a, t):
    """DOSE（plan §6.4）：激活集上 D_control = mean(D_new) + sd(D_new)/sd(D_Q)·(D_Q − mean(D_Q))，K = 旧 K + D_control；激活外 = 源 Q 账户 K。
    逐日；不可构造日 = DOSE_UNRESOLVED（当日回源 Q 账户 K 并计数）。"""
    Ks = native_q(k0, kQ, a)
    Kc = native_q(k0, kf_owner, a)
    out = Ks.copy()
    unres = 0
    days = 0
    ok = act & np.isfinite(k0) & np.isfinite(Ks) & np.isfinite(Kc)
    ix = np.flatnonzero(ok)
    if len(ix):
        tt = t[ix]
        bnd = np.flatnonzero(np.r_[True, tt[1:] != tt[:-1], True])
        for i0, i1 in zip(bnd[:-1], bnd[1:]):
            sl = ix[i0:i1]
            days += 1
            dq = Ks[sl] - k0[sl]
            dn = Kc[sl] - k0[sl]
            m = dose_match(dq, dn)
            if m is None:
                unres += 1
                continue
            out[sl] = k0[sl] + m
    return out, dict(dose_days=days, dose_unresolved_days=unres)


def cdose_K(k0, kQ, kf_owner, kf_ctrl, act, a, t):
    """COMPONENT_DOSE（plan §6.4a）：S_Q = 源 Q0 加记忆前 K；Δ_O = S_O − S_Q，Δ_G = S_G − S_Q；激活集上 Δ_D = mean(Δ_O) + sd(Δ_O)/sd(Δ_G)·(Δ_G − mean(Δ_G))，
    S_D = S_Q + Δ_D（不 clip，记越界率）；激活外 S_Q；不可构造日回 S_Q 并计数。"""
    SQ = native_q(k0, kQ, a)
    SO = native_q(k0, kf_owner, a)
    SG = native_q(k0, kf_ctrl, a)
    out = SQ.copy()
    unres = days = oob = n = 0
    ok = act & np.isfinite(SQ) & np.isfinite(SO) & np.isfinite(SG)
    ix = np.flatnonzero(ok)
    if len(ix):
        tt = t[ix]
        bnd = np.flatnonzero(np.r_[True, tt[1:] != tt[:-1], True])
        for i0, i1 in zip(bnd[:-1], bnd[1:]):
            sl = ix[i0:i1]
            days += 1
            m = dose_match(SG[sl] - SQ[sl], SO[sl] - SQ[sl])
            if m is None:
                unres += 1
                continue
            out[sl] = SQ[sl] + m
            oob += int(((out[sl] < 0) | (out[sl] > 1)).sum())
            n += len(sl)
    return out, dict(cdose_days=days, cdose_unresolved_days=unres, cdose_out_of_unit_share=(oob / n if n else 0.0))


def build(seg):
    import e6n_meas as ME
    t0 = time.time()
    B = Base(seg)
    S = ME.SegM(seg)
    if not (np.array_equal(S.t, B.t) and np.array_equal(S.c, B.c)):
        raise RuntimeError('测量单元与段上下文单元不一致')
    V = pd.read_csv(N.P('registry', 'input_variants_E6n.csv'), keep_default_na=False)
    vs = sorted(set(v for v in V.input_variant if v.split('|')[0] in ('RAW', 'CLONE', 'CLONE_RAW')))
    kd = os.path.join(B.d, 'kf')
    os.makedirs(kd, exist_ok=True)
    rows = []
    for v in vs:
        t1 = time.time()
        if v == 'CLONE_RAW':
            kf, info = clone_raw(B, S)
            act = np.zeros(B.n, bool)
        elif v.startswith('RAW'):
            kf, act, info = raw_kf(B, S, v)
        else:
            kf, act, info = clone_kf(B, S, v)
        p = os.path.join(kd, fname(v))
        tmp = p + '.tmp'
        with open(tmp, 'wb') as fh:
            np.save(fh, kf)
        os.replace(tmp, p)
        diff = np.isfinite(kf) & np.isfinite(B.kQ) & (kf != B.kQ)
        rows.append(dict(variant=v, file=os.path.basename(p), sha256=N.sha_file(p), n_cells=B.n, active_cells=int(act.sum()),
                         active_days=int(len(np.unique(B.t[act]))) if act.any() else 0, changed_vs_kQ=int(diff.sum()),
                         kf_finite=int(np.isfinite(kf).sum()), secs=round(time.time() - t1, 1), info=json.dumps(info, ensure_ascii=False)))
    M = pd.DataFrame(rows)
    N.atomic_write_csv(os.path.join(kd, 'kf_manifest.csv'), M)
    N.log('vars %s：%d 个变体，%.0f s；CLONE_RAW ≡ kQ：%s' % (seg, len(vs), time.time() - t0,
                                                       M.loc[M.variant == 'CLONE_RAW', 'info'].iloc[0] if (M.variant == 'CLONE_RAW').any() else 'NOT_RUN'))
    return M


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['build'])
    ap.add_argument('--seg', required=True)
    a = ap.parse_args()
    t0 = time.time()
    build(a.seg)
    N.write_receipt('E6n_vars_build_%s' % a.seg, [N.P('meas', a.seg, 'kf', 'kf_manifest.csv')], code=[__file__], secs=round(time.time() - t0, 1))


if __name__ == '__main__':
    main()
