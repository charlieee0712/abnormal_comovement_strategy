# -*- coding: utf-8 -*-
"""E6m N8 · B3 先行 · 格统计与对比（合同 §4–§6 + 附录 1）。一个进程处理一个 (段, 域[, 对比组])。
  cells     --seg S --dom D
  contrasts --seg S --dom D [--group all|DM|POSHL|POSM] [--paths 1024] [--max-days N]
  selfcheck：冻结 contrast 清单的 65 个 ID 恰好各被一个域的解析器认领一次（不读事件表）。
输出 stageN/B3_prelim/out/<段>__<域>/；执行端不读数值：日志与回执只有行数、状态计数、耗时。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_b3_kernels as K
from e6m_b3_build import YCOLS, HS, LABELS, ACT, PR_, POS, VOL, TREND, PEERQ, GAP, CVR, DOMAINS, wdir

MASK64 = (1 << 64) - 1
SMAP = {'HIGH-LOW': np.array([0, -1, 1], np.int8), 'HIGH-MID': np.array([-1, 0, 1], np.int8), 'MID-LOW': np.array([0, 1, -1], np.int8)}
SMAP_PEER = np.array([0, 1], np.int8)
HCOL = np.array([int(c.rsplit('_h', 1)[1]) for c in YCOLS])
LEVELS = ('U0', 'U1', 'U2')
MECHS = ('R_CELL_REMATCH', 'R_PAIR_SWAP')
VARCOL = {'A20_PRE': 'act20', 'A5_PRE': 'act5', 'A60_PRE': 'act60', 'PRE_R20': 'pos', 'DRAWDOWN_FROM_20D_HIGH': 'posdd',
          'VOL3': 'vol3', 'TREND3': 'trend', 'OVERNIGHT_GAP': 'gap', 'CVR_TAIL': 'cvr'}
BIG = np.int64(1) << 62


def odir(seg, dom, pilot=False):
    return M.P('stageN', 'B3_prelim', 'out_pilot' if pilot else 'out', '%s__%s' % (seg, dom))


def rss_gb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0 ** 2


def load_events(seg, dom):
    z = np.load(wdir('events_%s__%s.npz' % (seg, dom)), allow_pickle=False)
    return {k: z[k] for k in z.files}


def nw(x, L):
    """Newey–West（Bartlett，lag L）均值标准误；x 只取有限值（段内有值日压缩序列，附录 1 B-11）。返回 (均值, se, 有值日数)。"""
    x = x[np.isfinite(x)]
    n = len(x)
    if n == 0:
        return np.nan, np.nan, 0
    mu = float(x.mean())
    if n < 2:
        return mu, np.nan, n
    e = x - mu
    s = e @ e / n
    for k in range(1, min(L, n - 1) + 1):
        s += 2.0 * (1.0 - k / (L + 1.0)) * (e[k:] @ e[:-k]) / n
    return mu, float(np.sqrt(max(s, 0.0) / n)), n


# ---------------------------------------------------------------- cells
def cell_mask(E, r):
    m = E[VARCOL[r.activity_var]] == ACT[r.activity]
    if r.price_reaction != 'ALL':
        m &= E['pr'] == PR_[r.price_reaction]
    if r.position_var != 'NONE':
        m &= E[VARCOL[r.position_var]] == POS[r.position]
    if r.state_var != 'NONE':
        m &= E[VARCOL[r.state_var]] == (VOL if r.state_var == 'VOL3' else TREND)[r.state]
    if r.peer_quadrant != 'ALL':
        m &= E['peerq'] == PEERQ[r.peer_quadrant]
    if r.extra_var != 'NONE':
        m &= E[VARCOL[r.extra_var]] == (GAP if r.extra_var == 'OVERNIGHT_GAP' else CVR)[r.extra]
    return m


def spells(t, tick):
    if len(t) == 0:
        return 0
    o = np.lexsort((t, tick))
    tt, kk = t[o], tick[o]
    new = np.ones(len(t), bool)
    new[1:] = (kk[1:] != kk[:-1]) | (tt[1:] != tt[:-1] + 1)
    return int(new.sum())


def task_cells(seg, dom):
    t0 = time.time()
    E = load_events(seg, dom)
    reg = M.read_csv_keep(M.P('registry', 'b3_cells_E6m.csv'), dtype=str)
    reg = reg[reg.domain == dom].reset_index(drop=True)
    days = np.flatnonzero(E['ndom'] > 0)
    D = len(days)
    pos_of = np.full(len(E['ndom']), -1, np.int64)
    pos_of[days] = np.arange(D)
    ndom_tot = int(E['ndom'][days].sum())
    blocks = [('OWN', E['Y'])] + ([('POOL0_BRIDGE', E['YB'])] if 'YB' in E else [])
    NC = len(YCOLS)
    nday = np.zeros((len(reg), D), np.int32)
    mday = {b: np.full((len(reg), D, NC), np.nan) for b, _ in blocks}
    cday = {b: np.zeros((len(reg), D, NC), np.int32) for b, _ in blocks}
    rows = []
    for ci, r in enumerate(reg.itertuples(index=False)):
        ix = np.flatnonzero(cell_mask(E, r))
        p = pos_of[E['t'][ix]]
        nday[ci] = np.bincount(p, minlength=D)
        n_ev = len(ix)
        n_sp = spells(E['t'][ix], E['tick'][ix])
        n_cash = int(E['cash'][ix].sum())
        n_dates = int((nday[ci] > 0).sum())
        for b, Yall in blocks:
            Y = Yall[ix]
            fin = np.isfinite(Y)
            for j, col in enumerate(YCOLS):
                s = np.bincount(p, weights=np.where(fin[:, j], Y[:, j], 0.0), minlength=D)
                c = np.bincount(p, weights=fin[:, j].astype(float), minlength=D).astype(np.int64)
                md = np.full(D, np.nan)
                np.divide(s, c, out=md, where=c > 0)
                mday[b][ci, :, j] = md
                cday[b][ci, :, j] = c
                mu, se, nd = nw(md, int(HCOL[j]))
                q = np.percentile(Y[fin[:, j], j], [5, 25, 50, 75, 95]) if fin[:, j].any() else [np.nan] * 5
                lab, h = col.rsplit('_h', 1)
                rows.append(dict(segment=seg, domain=dom, cell_id=r.cell_id, family=r.family, benchmark=b, label=lab, h=int(h),
                                 status='COMPUTED' if n_ev else 'EMPTY_CELL', n_dates=n_dates, n_events=n_ev, n_spells=n_sp,
                                 domain_share=(n_ev / ndom_tot) if ndom_tot else np.nan, n_cash_events=n_cash, n_label_finite=int(fin[:, j].sum()),
                                 missing_rate=(1.0 - fin[:, j].mean()) if n_ev else np.nan, n_days_defined=nd, mean_bp_per_h=mu,
                                 hac_se_bp_per_h=se, hac_lag=int(h), q05_bp_per_h=q[0], q25_bp_per_h=q[1], q50_bp_per_h=q[2],
                                 q75_bp_per_h=q[3], q95_bp_per_h=q[4]))
    # UNKNOWN 单列（状态 / 同业）：只计数
    unk = []
    base_fams = (('F3_QUIETxPOSxVOL', 'vol3', 'VOL3', PR_['QUIET']), ('F4_QUIETxPOSxTREND', 'trend', 'TREND3', PR_['QUIET']),
                 ('F5_UPxPOSxVOL', 'vol3', 'VOL3', PR_['UP']))
    for fam, sv, svn, prc in base_fams:
        for a in ACT:
            for pz in POS:
                base = (E['act20'] == ACT[a]) & (E['pr'] == prc) & (E['pos'] == POS[pz])
                un = base & (E[sv] < 0)
                unk.append(dict(segment=seg, domain=dom, family=fam, activity=a, position=pz, extra_var=svn, n_events_base=int(base.sum()),
                                n_events_unknown=int(un.sum()), n_dates_unknown=int(len(np.unique(E['t'][un])))))
    for a in ACT:
        base = (E['act20'] == ACT[a]) & (E['pr'] == PR_['QUIET'])
        un = base & (E['peerq'] < 0)
        unk.append(dict(segment=seg, domain=dom, family='F6_QUIETxPEER', activity=a, position='ALL', extra_var='PEER_QUADRANT',
                        n_events_base=int(base.sum()), n_events_unknown=int(un.sum()), n_dates_unknown=int(len(np.unique(E['t'][un])))))
    od = odir(seg, dom)
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'cells_summary.csv')
    p2 = os.path.join(od, 'cells_unknown_counts.csv')
    p3 = os.path.join(od, 'cells_daily.npz')
    df = pd.DataFrame(rows)
    M.atomic_write_csv(p1, df)
    M.atomic_write_csv(p2, pd.DataFrame(unk))
    M.atomic_write_npz(p3, cell_ids=reg.cell_id.to_numpy(str), days=days, ycols=np.array(YCOLS), n_day=nday,
                       **{'mean_%s' % b: mday[b] for b, _ in blocks}, **{'cnt_%s' % b: cday[b] for b, _ in blocks})
    st = df.drop_duplicates('cell_id').status.value_counts().to_dict()
    T = dict(cells=len(reg), days=D, rows=len(df), cell_status=st, wall_s=round(time.time() - t0, 1), rss_peak_gb=round(rss_gb(), 2))
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_cells_%s__%s' % (seg, dom)), [p1, p2, p3], status='SUCCEEDED',
                    code=[__file__, M.__file__], **T)
    print(json.dumps(dict(seg=seg, dom=dom, **T), ensure_ascii=False), flush=True)
    return 0


# ---------------------------------------------------------------- contrasts：清单解析
def parse_specs(dom, ids):
    specs = {}
    for cid in ids:
        p = cid.split('|')
        card = p[1]
        if card == 'Q12':
            if dom != 'POOL0':
                continue
            if p[2] == 'CVR':
                specs[cid] = dict(kind='ACT', cond=dict(cvr=1, pos=POS[p[3].split('=')[1]]), side='act20', smap=SMAP['HIGH-LOW'], dm=False)
            elif p[2] == 'GAP':
                specs[cid] = dict(kind='ACT', cond=dict(gap=GAP[p[3]], pos=POS[p[4].split('=')[1]]), side='act20', smap=SMAP[p[5]], dm=False)
            continue
        if p[2] != dom:
            continue
        if card == 'Q09':
            specs[cid] = dict(kind='Q09')
        elif card == 'Q11':
            specs[cid] = dict(kind='Q11', cond=dict(pr=PR_['QUIET'], act20=ACT['LOW'], sstrong=0), side='pstrong', smap=SMAP_PEER, dm=False)
        elif card == 'Q10':
            if p[4].startswith('POS='):
                specs[cid] = dict(kind='ACT', cond=dict(pr=PR_['QUIET'], pos=POS[p[4].split('=')[1]]), side='act20', smap=SMAP[p[5]], dm=False)
            elif p[4].startswith('DID_POS'):
                specs[cid] = dict(kind='DID', comps=('B3C|Q10|%s|QUIET|POS=HIGH|HIGH-LOW' % dom, 'B3C|Q10|%s|QUIET|POS=LOW|HIGH-LOW' % dom))
            elif len(p) > 5 and p[5] == 'D_MATCHED':
                specs[cid] = dict(kind='ACT', cond=dict(pr=PR_[p[3]]), side='act20', smap=SMAP['HIGH-LOW'], dm=True)
    return specs


def level_mode(spec, level, dom):
    """UNPAIRED / PAIRED / NOT_APPLICABLE / DEGENERATE_CONDITIONAL_CONTROL（合同 §5 与附录 1 B-5）。"""
    k = spec['kind']
    if k == 'Q09':
        return 'UNPAIRED' if (level == 'U0' and dom != 'CLEAN') else 'NOT_APPLICABLE'
    if k == 'Q11':
        return 'UNPAIRED' if level == 'U0' else 'DEGENERATE_CONDITIONAL_CONTROL'
    if level == 'U2' and dom == 'CLEAN':
        return 'NOT_APPLICABLE'
    if level == 'U0':
        return 'PAIRED' if spec.get('dm') else 'UNPAIRED'
    return 'PAIRED'


def mech_mode(spec, mode):
    if spec['kind'] == 'Q09' or mode in ('NOT_APPLICABLE', 'DEGENERATE_CONDITIONAL_CONTROL'):
        return {m: 'NOT_APPLICABLE' for m in MECHS} if spec['kind'] == 'Q09' or mode == 'NOT_APPLICABLE' else {m: mode for m in MECHS}
    return {'R_CELL_REMATCH': 'RUN', 'R_PAIR_SWAP': 'RUN' if mode == 'PAIRED' else 'NOT_APPLICABLE'}


GROUPS = {'DMUP': lambda cid, s: bool(s.get('dm')) and '|UP|' in cid,
          'DMDN': lambda cid, s: bool(s.get('dm')) and '|DOWN|' in cid,
          'MISC': lambda cid, s: s['kind'] in ('Q09', 'Q11') or cid.split('|')[1] == 'Q12',
          'POSHL': lambda cid, s: s['kind'] == 'DID' or ('|POS=HIGH|' in cid or '|POS=LOW|' in cid) and cid.split('|')[1] == 'Q10',
          'POSM': lambda cid, s: '|POS=MID|' in cid and cid.split('|')[1] == 'Q10'}


def task_selfcheck():
    reg = M.read_csv_keep(M.P('registry', 'b3_contrasts_E6m.csv'), dtype=str)
    ids = list(reg.contrast_id.unique())
    claim = {}
    for dom in DOMAINS:
        for cid in parse_specs(dom, ids):
            claim.setdefault(cid, []).append(dom)
    miss = [c for c in ids if c not in claim]
    dup = [c for c, v in claim.items() if len(v) > 1]
    grp = {}
    for dom in DOMAINS:
        sp = parse_specs(dom, ids)
        for cid, s in sp.items():
            g = [k for k, f in GROUPS.items() if f(cid, s)]
            grp[cid] = g
    gbad = [c for c, g in grp.items() if len(g) != 1]
    ok = not miss and not dup and not gbad and len(ids) == 65
    print(json.dumps(dict(ids=len(ids), claimed=len(claim), missing=miss, duplicated=dup, group_not_unique=gbad, ok=ok), ensure_ascii=False))
    return 0 if ok else 1


# ---------------------------------------------------------------- contrasts：逐日计算
def strata(Ed, level, dm):
    """返回分层键（−1 = 不可分层）。"""
    d = Ed['d']
    fin = np.isfinite(d)
    if level == 'U0':
        return np.where(fin, 0, -1).astype(np.int64) if dm else None
    ok = fin & (Ed['ind'] >= 0) & (Ed['size3'] >= 0)
    key = Ed['ind'].astype(np.int64) * 3 + Ed['size3'].astype(np.int64)
    if level == 'U2':
        ok &= Ed['k3'] >= 0
        key = key * 3 + Ed['k3'].astype(np.int64)
    return np.where(ok, key, -1)


def arrange(Ed, key):
    """可分层成员按 (层, d, ticker) 放前段、不可分层放后段；返回 (排序下标, off)。"""
    ks = np.where(key >= 0, key, BIG)
    dfill = np.where(np.isfinite(Ed['d']), Ed['d'], 0.0)
    o = np.lexsort((Ed['tick'], dfill, ks))
    ko = ks[o]
    ns = int((ko < BIG).sum())
    if ns:
        ch = np.flatnonzero(np.diff(ko[:ns])) + 1
        off = np.r_[0, ch, ns].astype(np.int64)
    else:
        off = np.zeros(1, np.int64)
    return o, off, dfill[o]


class Acc(object):
    """一个 (对比, 层, 机制) 的随机累加器：每路径全期日均（可估子集 / 严格）与逐日跨路径均值。"""

    def __init__(self, P, D, C, strict):
        self.se = np.zeros((P, C))
        self.ce = np.zeros((P, C), np.int64)
        self.de = np.full((D, C), np.nan)
        self.strict = strict
        if strict:
            self.ss = np.zeros((P, C))
            self.cs = np.zeros((P, C), np.int64)
            self.ds = np.full((D, C), np.nan)

    @staticmethod
    def _add(s, c, dd, di, x):
        f = np.isfinite(x)
        s += np.where(f, x, 0.0)
        c += f
        nf = f.sum(0)
        tot = np.where(f, x, 0.0).sum(0)
        dd[di] = np.where(nf > 0, tot / np.maximum(nf, 1), np.nan)

    def add(self, di, est, strict):
        self._add(self.se, self.ce, self.de, di, est)
        if self.strict:
            self._add(self.ss, self.cs, self.ds, di, strict)


def task_contrasts(seg, dom, group, P, max_days):
    t0 = time.time()
    E = load_events(seg, dom)
    reg = M.read_csv_keep(M.P('registry', 'b3_contrasts_E6m.csv'), dtype=str)
    ids = list(reg.contrast_id.unique())
    specs = parse_specs(dom, ids)
    if group != 'all':
        specs = {c: s for c, s in specs.items() if GROUPS[group](c, s)}
        for c, s in list(specs.items()):                     # DiD 的分量同组
            if s['kind'] == 'DID':
                for cc in s['comps']:
                    if cc not in specs:
                        specs[cc] = parse_specs(dom, [cc])[cc]
    days = np.flatnonzero(E['ndom'] > 0)
    if max_days:
        days = days[:max_days]
    D = len(days)
    NC = len(YCOLS)
    dstart = np.searchsorted(E['t'], days, 'left')
    dend = np.searchsorted(E['t'], days, 'right')
    seeds = {}
    for cid in specs:
        for lv in LEVELS:
            for mc in MECHS:
                seeds[(cid, lv, mc)] = np.uint64(M.stable_seed_int('E6m-B3', mc, cid, lv) & MASK64)
    modes = {(cid, lv): level_mode(s, lv, dom) for cid, s in specs.items() for lv in LEVELS}
    real_e, real_s, diag, acc = {}, {}, {}, {}
    for (cid, lv), md in modes.items():
        if md in ('UNPAIRED', 'PAIRED'):
            real_e[(cid, lv)] = np.full((D, NC), np.nan)
            if md == 'PAIRED':
                real_s[(cid, lv)] = np.full((D, NC), np.nan)
            diag[(cid, lv)] = np.zeros((D, 8), np.float64)  # n_high, n_low, n_other, n_nonstrat, npair, sum_dist, unmatched_high, unmatched_low
            if specs[cid]['kind'] != 'Q09':
                for mc, run in mech_mode(specs[cid], md).items():
                    if run == 'RUN':
                        acc[(cid, lv, mc)] = Acc(P, D, NC, strict=(md == 'PAIRED'))
    q09 = {cid: dict(cnt=np.zeros((D, 5), np.int64), mean=np.full((D, 3, NC), np.nan)) for cid, s in specs.items()
           if s['kind'] == 'Q09' and dom != 'CLEAN'}
    order_ids = [c for c, s in specs.items() if s['kind'] in ('ACT', 'Q11')] + [c for c, s in specs.items() if s['kind'] == 'DID']
    kern_s = 0.0
    for di in range(D):
        a, b = dstart[di], dend[di]
        Ed = {k: E[k][a:b] for k in ('tick', 'ind', 'size3', 'k3', 'act20', 'pr', 'pos', 'sstrong', 'pstrong', 'cvr', 'gap', 'qgood', 'd')}
        Yd = E['Y'][a:b]
        tglob = int(days[di])
        block = tglob // 5
        day_out = {}
        for cid in order_ids:
            s = specs[cid]
            if s['kind'] == 'DID':
                cH, cL = s['comps']
                for lv in LEVELS:
                    md = modes[(cid, lv)]
                    if md not in ('UNPAIRED', 'PAIRED'):
                        continue
                    oh, ol = day_out.get((cH, lv)), day_out.get((cL, lv))
                    if oh is None or ol is None:
                        continue
                    real_e[(cid, lv)][di] = oh['e'] - ol['e']
                    if md == 'PAIRED':
                        real_s[(cid, lv)][di] = oh['s'] - ol['s']
                    for mc in MECHS:
                        if (cid, lv, mc) in acc and mc in oh['R'] and mc in ol['R']:
                            eh, sh_ = oh['R'][mc]
                            el, sl_ = ol['R'][mc]
                            acc[(cid, lv, mc)].add(di, eh - el, (sh_ - sl_) if sh_ is not None else None)
                continue
            m = np.ones(b - a, bool)
            for v, code in s['cond'].items():
                m &= Ed[v] == code
            code_all = Ed[s['side']]
            m &= code_all >= 0
            rix = np.flatnonzero(m)
            if len(rix) == 0:
                continue
            sub = {k: v[rix] for k, v in Ed.items()}
            Ys = Yd[rix]
            for lv in LEVELS:
                md = modes[(cid, lv)]
                if md not in ('UNPAIRED', 'PAIRED'):
                    continue
                key = strata(sub, lv, s.get('dm', False))
                if key is None:
                    key = np.full(len(rix), -1, np.int64)
                o, off, dsort = arrange(sub, key)
                code = np.ascontiguousarray(sub[s['side']][o]).astype(np.int8)
                tk = np.ascontiguousarray(sub['tick'][o]).astype(np.int64)
                Yo = np.ascontiguousarray(Ys[o])
                recv = np.argsort(tk, kind='mergesort').astype(np.int64)
                lab = K.sides_of(code, s['smap'])
                nh, nl = int((lab == 1).sum()), int((lab == 0).sum())
                nonstrat = int(len(o) - off[-1])
                out = dict(R={})
                tk0 = time.time()
                if md == 'PAIRED':
                    n = len(o)
                    ph = np.empty(n, np.int64)
                    pl = np.empty(n, np.int64)
                    npair, s_sum, s_cnt, s_nan = K.match_day(off, dsort, lab, Yo, ph, pl)
                    with np.errstate(all='ignore'):
                        e = np.where(s_cnt > 0, s_sum / np.maximum(s_cnt, 1), np.nan)
                        st = np.where((npair > 0) & ~s_nan, s_sum / max(npair, 1), np.nan)
                    dist = float(np.abs(dsort[ph[:npair]] - dsort[pl[:npair]]).sum()) if npair else 0.0
                    real_e[(cid, lv)][di] = e
                    real_s[(cid, lv)][di] = st
                    out.update(e=e, s=st)
                    diag[(cid, lv)][di] = (nh, nl, len(o) - nh - nl, nonstrat, npair, dist, nh - npair, nl - npair)
                    if (cid, lv, 'R_CELL_REMATCH') in acc:
                        er, sr = K.paths_rematch(off, dsort, code, s['smap'], Yo, tk, recv, seeds[(cid, lv, 'R_CELL_REMATCH')], block, P, True)
                        acc[(cid, lv, 'R_CELL_REMATCH')].add(di, er, sr)
                        out['R']['R_CELL_REMATCH'] = (er, sr)
                    if (cid, lv, 'R_PAIR_SWAP') in acc:
                        es, ss = K.paths_pairswap(ph, pl, npair, Yo, tk, seeds[(cid, lv, 'R_PAIR_SWAP')], block, P)
                        acc[(cid, lv, 'R_PAIR_SWAP')].add(di, es, ss)
                        out['R']['R_PAIR_SWAP'] = (es, ss)
                else:
                    e = K.means_diff(lab, Yo)
                    real_e[(cid, lv)][di] = e
                    out.update(e=e, s=None)
                    diag[(cid, lv)][di] = (nh, nl, len(o) - nh - nl, nonstrat, 0, 0.0, 0, 0)
                    if (cid, lv, 'R_CELL_REMATCH') in acc:
                        er, _ = K.paths_rematch(off, dsort, code, s['smap'], Yo, tk, recv, seeds[(cid, lv, 'R_CELL_REMATCH')], block, P, False)
                        acc[(cid, lv, 'R_CELL_REMATCH')].add(di, er, None)
                        out['R']['R_CELL_REMATCH'] = (er, None)
                kern_s += time.time() - tk0
                day_out[(cid, lv)] = out
        for cid, qq in q09.items():
            ok = (Ed['pr'] >= 0) & (Ed['qgood'] >= 0)
            Q = Ed['pr'] == PR_['QUIET']
            G = Ed['qgood'] == 1
            grp = (ok & Q & G, ok & Q & ~G, ok & ~Q & G, ok & ~Q & ~G)
            qq['cnt'][di] = [int(g.sum()) for g in grp] + [int((~ok).sum())]
            for gi in range(3):
                Yg = Yd[grp[gi]]
                f = np.isfinite(Yg)
                n_ = f.sum(0)
                with np.errstate(all='ignore'):
                    qq['mean'][di, gi] = np.where(n_ > 0, np.where(f, Yg, 0.0).sum(0) / np.maximum(n_, 1), np.nan)
            real_e[(cid, 'U0')][di] = qq['mean'][di, 1] - qq['mean'][di, 2]   # 只 QUIET − 只 Q 优
    # ---- 汇总与写出
    od = odir(seg, dom, pilot=bool(max_days))
    os.makedirs(od, exist_ok=True)
    tag = '' if group == 'all' else '_' + group
    rows_r, rows_rand, rows_diag, rows_status = [], [], [], []
    want = set(specs) if group == 'all' else {c for c, s in specs.items() if GROUPS[group](c, s)}
    for (cid, lv), md in modes.items():
        if cid not in want:
            continue
        if md not in ('UNPAIRED', 'PAIRED'):
            for mc in MECHS:
                rows_status.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv, random_id=mc, real_status=md, random_status=md))
            continue
        versions = [('MEAN_ESTIMABLE' if md == 'UNPAIRED' else 'ESTIMABLE_SUBSET', real_e[(cid, lv)])]
        if md == 'PAIRED':
            versions.append(('STRICT', real_s[(cid, lv)]))
        any_def = False
        for vn, arr in versions:
            for j, col in enumerate(YCOLS):
                mu, se, nd = nw(arr[:, j], int(HCOL[j]))
                any_def |= nd > 0
                lab_, h = col.rsplit('_h', 1)
                rows_r.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv, version=vn, label=lab_, h=int(h), n_days_defined=nd,
                                   mean_bp_per_h=mu, hac_se_bp_per_h=se, hac_lag=int(h), status='COMPUTED' if nd else 'DEGENERATE_CONDITIONAL_CONTROL'))
        dg = diag[(cid, lv)]
        if specs[cid]['kind'] in ('DID', 'Q09'):
            # DiD / Q09 没有自己的配对诊断（逐日循环里不写 diag；N8 erratum 1）：只报有值日数，配对计数以分量行 / q09_crosstab 为准
            rows_diag.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv,
                                  mode='DID_FROM_COMPONENTS' if specs[cid]['kind'] == 'DID' else 'Q09_CROSSTAB', days=D,
                                  days_with_value=int(np.isfinite(real_e[(cid, lv)]).any(axis=1).sum())))
        else:
          rows_diag.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv, mode=md, days=D, days_with_legal=int(((dg[:, 0] + dg[:, 1] + dg[:, 2]) > 0).sum()),
                              days_with_pairs=int((dg[:, 4] > 0).sum()), legal_high=int(dg[:, 0].sum()), legal_low=int(dg[:, 1].sum()), legal_other=int(dg[:, 2].sum()),
                              non_stratifiable=int(dg[:, 3].sum()), pairs=int(dg[:, 4].sum()), mean_pair_abs_d=(dg[:, 5].sum() / dg[:, 4].sum()) if dg[:, 4].sum() else np.nan,
                              unmatched_high=int(dg[:, 6].sum()), unmatched_low=int(dg[:, 7].sum())))
        mm = mech_mode(specs[cid], md)
        for mc in MECHS:
            if (cid, lv, mc) in acc:
                rs = 'COMPUTED' if int(acc[(cid, lv, mc)].ce.sum()) > 0 else 'DEGENERATE_CONDITIONAL_CONTROL'   # 有值才算 COMPUTED
            else:
                rs = mm.get(mc, 'NOT_APPLICABLE')
            rows_status.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv, random_id=mc,
                                    real_status='COMPUTED' if any_def else 'DEGENERATE_CONDITIONAL_CONTROL', random_status=rs))
    npz_r = {}
    for (cid, lv), arr in real_e.items():
        if cid in want:
            npz_r['%s#%s#E' % (cid, lv)] = arr
    for (cid, lv), arr in real_s.items():
        if cid in want:
            npz_r['%s#%s#S' % (cid, lv)] = arr
    npz_p, npz_d = {}, {}
    for (cid, lv, mc), A in acc.items():
        if cid not in want:
            continue
        for vn, s_, c_, d_ in (('ESTIMABLE_SUBSET' if A.strict else 'MEAN_ESTIMABLE', A.se, A.ce, A.de),) + ((('STRICT', A.ss, A.cs, A.ds),) if A.strict else ()):
            with np.errstate(all='ignore'):
                pm = np.where(c_ > 0, s_ / np.maximum(c_, 1), np.nan)
            npz_p['%s#%s#%s#%s' % (cid, lv, mc, vn)] = pm
            npz_d['%s#%s#%s#%s' % (cid, lv, mc, vn)] = d_
            for j, col in enumerate(YCOLS):
                v = pm[:, j]
                f = np.isfinite(v)
                lab_, h = col.rsplit('_h', 1)
                rows_rand.append(dict(segment=seg, domain=dom, contrast_id=cid, matching_id=lv, random_id=mc, version=vn, label=lab_, h=int(h),
                                      paths=P, paths_defined=int(f.sum()), path_days_defined_median=float(np.median(c_[:, j])),
                                      mean_of_path_means_bp_per_h=float(v[f].mean()) if f.any() else np.nan,
                                      sd_of_path_means_bp_per_h=float(v[f].std(ddof=1)) if f.sum() > 1 else np.nan,
                                      mcse_bp_per_h=float(v[f].std(ddof=1) / np.sqrt(f.sum())) if f.sum() > 1 else np.nan,
                                      q025_bp_per_h=float(np.percentile(v[f], 2.5)) if f.any() else np.nan,
                                      q05_bp_per_h=float(np.percentile(v[f], 5)) if f.any() else np.nan,
                                      q50_bp_per_h=float(np.percentile(v[f], 50)) if f.any() else np.nan,
                                      q95_bp_per_h=float(np.percentile(v[f], 95)) if f.any() else np.nan,
                                      q975_bp_per_h=float(np.percentile(v[f], 97.5)) if f.any() else np.nan,
                                      status='COMPUTED' if f.any() else 'DEGENERATE_CONDITIONAL_CONTROL'))
    outs = []
    for name, df in (('contrasts_real%s.csv' % tag, pd.DataFrame(rows_r)), ('contrasts_random%s.csv' % tag, pd.DataFrame(rows_rand)),
                     ('contrasts_pairs%s.csv' % tag, pd.DataFrame(rows_diag)), ('contrasts_status%s.csv' % tag, pd.DataFrame(rows_status))):
        p = os.path.join(od, name)
        M.atomic_write_csv(p, df)
        outs.append(p)
    for name, dct in (('contrasts_real_daily%s.npz' % tag, npz_r), ('contrasts_random_pathmeans%s.npz' % tag, npz_p),
                      ('contrasts_random_daily%s.npz' % tag, npz_d)):
        p = os.path.join(od, name)
        M.atomic_write_npz(p, days=days, ycols=np.array(YCOLS), **dct)
        outs.append(p)
    for cid, qq in q09.items():
        if cid not in want:
            continue
        tot = qq['cnt'].sum(0)
        p = os.path.join(od, 'q09_crosstab%s.csv' % tag)
        M.atomic_write_csv(p, pd.DataFrame([dict(segment=seg, domain=dom, contrast_id=cid, n_quiet_and_qgood=int(tot[0]), n_only_quiet=int(tot[1]),
                                                  n_only_qgood=int(tot[2]), n_neither=int(tot[3]), n_excluded_unknown=int(tot[4]), days=D)]))
        outs.append(p)
        p = os.path.join(od, 'q09_daily%s.npz' % tag)
        M.atomic_write_npz(p, days=days, ycols=np.array(YCOLS), counts=qq['cnt'], group_means=qq['mean'],
                           groups=np.array(['QUIET_AND_QGOOD', 'ONLY_QUIET', 'ONLY_QGOOD']))
        outs.append(p)
    stc = pd.DataFrame(rows_status)
    T = dict(group=group, contrasts=len(want), days=D, paths=P, real_rows=len(rows_r), random_rows=len(rows_rand),
             status_real=stc.real_status.value_counts().to_dict() if len(stc) else {}, status_random=stc.random_status.value_counts().to_dict() if len(stc) else {},
             kernel_s=round(kern_s, 1), wall_s=round(time.time() - t0, 1), rss_peak_gb=round(rss_gb(), 2), max_days=max_days)
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_b3_contrasts_%s__%s%s' % (seg, dom, tag)), outs, status='SUCCEEDED', code=[__file__, K.__file__, M.__file__], **T)
    print(json.dumps(dict(seg=seg, dom=dom, **T), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['cells', 'contrasts', 'selfcheck'])
    ap.add_argument('--seg')
    ap.add_argument('--dom')
    ap.add_argument('--group', default='all', choices=['all'] + list(GROUPS))
    ap.add_argument('--paths', type=int, default=1024)
    ap.add_argument('--max-days', type=int, default=0)
    a = ap.parse_args()
    if a.task == 'selfcheck':
        sys.exit(task_selfcheck())
    sys.exit(task_cells(a.seg, a.dom) if a.task == 'cells' else task_contrasts(a.seg, a.dom, a.group, a.paths, a.max_days))
