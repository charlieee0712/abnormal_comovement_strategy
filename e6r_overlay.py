# -*- coding: utf-8 -*-
"""E6r 形成层（plan §4.3 / §6.1 第一层；brief §0.1 #12–#14、C5–C7）：每个 (form, memory) 的源最终 cohort（形成名单 CSR，与 e6r_acct.Market.formation 同序）逐形成日：
- 标签（tie-aware 中点秩三分位，plan 附录 C tertiles；有限值 < 3 或全同 → 全 NA；缺失 → NA；不按 ID 拆平局）：
  lab20 = CVR20_risk 原值（高 = 坏 → 低值 T1 得 +λ）、lab5 = CVR5、labsz = clean 市值分位（zsize，小盘 T1）、labcell = 格（iskid = 行业 × clean 市值三档）内 CVR20；
  na 原因（0 已分组 / 1 缺失 / 2 有限值 < 3 / 3 全同）分族记录（entry_tertiles 用）。
- T0 状态 st0 = T1b_LEVEL 面板形成日收盘值（1 BAD / 0 GOOD / −1 UNKNOWN；UNKNOWN 不当 BAD）；cell = iskid（−1 未知）。
- 八个算子的形成目标与 ρ = w*/b（e6r_kl.form_tilt，与引擎随机路径同一函数）：GATE_STATE / DROP_T3（ρ ∈ {0, 1}；pin = 测量未知 = 随机门不可删）、
  TILT_CVR_L050 / L025 / TILT_SIZE_L050 / TILT_CVR5_L050（q = b(1 + λs)，KL 投影到 Σb：单股 .015、行业 ind_share + .03、NA 固定）、
  GATE_TILT（先冻结原 cohort CVR20 标签，再门掉 T0 BAD，再在保留集倾斜）、TILT_CVR_CELL_L050（每格内倾斜、格预算 = Σ_cell b、未知格固定）。
- 形成层逐日统计（weights_E6r FORMATION 层 / allocation_projection）：g、h2、h1.5、N_eff = g²/h2、legacy 1/h2、形状代理 h1.5/g、转移份额 Σmax(w − b, 0)/g、
  单股 / 行业上界绑定份额、投影状态与违约。
输出 <cache>/overlay/<form>|<mem>.npz。不读收益。用法：python3 e6r_overlay.py"""
import os
import json
import time
import resource

import numpy as np
from numba import njit

import e6r_core as O
import e6r_kl as KL
from e6r_kl import tertile_codes, form_tilt
import e6r_acct as A

SCHEMES = ('GATE_STATE', 'DROP_T3', 'TILT_CVR_L050', 'TILT_CVR_L025', 'TILT_SIZE_L050', 'TILT_CVR5_L050', 'GATE_TILT', 'TILT_CVR_CELL_L050')
NSTAT = 12   # g, h2, h15, neff, inv_s2, shape, transfer, cap_bound_share, ind_bound_share, status, capviol, indviol


@njit(cache=True)
def _labels(a, b, vals, out, why):
    m = b - a
    v = np.empty(m)
    for i in range(m):
        v[i] = vals[i]
    lab = np.zeros(m, np.int64)
    r = tertile_codes(v, m, lab)
    for i in range(m):
        out[a + i] = lab[i]
        if not np.isfinite(v[i]):
            why[a + i] = 1
        elif r == 1:
            why[a + i] = 2
        elif r == 2:
            why[a + i] = 3
        else:
            why[a + i] = 0


@njit(cache=True)
def build(ptr, col, w, cvr20, cvr5, zsz, lvl, iskid, ind, capsh, idev, rcap, T,
          lab20, lab5, labsz, labcell, why20, why5, whysz, whycell, st0, cell, rho, pin, stats):
    G = capsh.shape[1]
    for d in range(T):
        a, b = ptr[d], ptr[d + 1]
        m = b - a
        if m == 0:
            continue
        v20 = np.empty(m)
        v5 = np.empty(m)
        vsz = np.empty(m)
        bb = np.empty(m)
        grp = np.empty(m, np.int64)
        cl = np.empty(m, np.int64)
        u = np.full(m, rcap)
        for i in range(m):
            s = col[a + i]
            v20[i] = cvr20[d, s]
            v5[i] = cvr5[d, s]
            vsz[i] = zsz[d, s]
            bb[i] = w[a + i]
            grp[i] = ind[d, s]
            cl[i] = iskid[d, s] if ind[d, s] >= 0 else -1
            st0[a + i] = lvl[d, s]
            cell[a + i] = cl[i]
        _labels(a, b, v20, lab20, why20)
        _labels(a, b, v5, lab5, why5)
        _labels(a, b, vsz, labsz, whysz)
        # 格内 CVR20 三分位（未知格 → NA，原因 = 1 缺失）
        order = np.argsort(cl, kind='mergesort')
        k0 = 0
        while k0 < m:
            c = cl[order[k0]]
            k1 = k0
            while k1 < m and cl[order[k1]] == c:
                k1 += 1
            nn = k1 - k0
            if c < 0:
                for t in range(k0, k1):
                    labcell[a + order[t]] = 0
                    whycell[a + order[t]] = 1
            else:
                vv = np.empty(nn)
                for t in range(nn):
                    vv[t] = v20[order[k0 + t]]
                lab = np.zeros(nn, np.int64)
                r = tertile_codes(vv, nn, lab)
                for t in range(nn):
                    i = order[k0 + t]
                    labcell[a + i] = lab[t]
                    if not np.isfinite(vv[t]):
                        whycell[a + i] = 1
                    elif r == 1:
                        whycell[a + i] = 2
                    elif r == 2:
                        whycell[a + i] = 3
                    else:
                        whycell[a + i] = 0
            k0 = k1
        gcap = np.empty(G)
        for g in range(G):
            gcap[g] = capsh[d, g] + idev
        g0 = 0.0
        for i in range(m):
            g0 += bb[i]
        for sc in range(8):
            keep = np.ones(m)
            labv = np.zeros(m, np.int64)
            pn = np.zeros(m, np.bool_)
            wr = np.empty(m)
            st = 0
            lam = 0.5
            cells_on = False
            if sc == 0:                                   # GATE_STATE
                for i in range(m):
                    wr[i] = 0.0 if st0[a + i] == 1 else bb[i]
                    pn[i] = st0[a + i] < 0
            elif sc == 1:                                 # DROP_T3
                for i in range(m):
                    wr[i] = 0.0 if lab20[a + i] == 3 else bb[i]
                    pn[i] = lab20[a + i] == 0
            else:
                if sc == 2 or sc == 3 or sc == 6:
                    for i in range(m):
                        labv[i] = lab20[a + i]
                elif sc == 4:
                    for i in range(m):
                        labv[i] = labsz[a + i]
                elif sc == 5:
                    for i in range(m):
                        labv[i] = lab5[a + i]
                else:
                    for i in range(m):
                        labv[i] = labcell[a + i]
                    cells_on = True
                if sc == 3:
                    lam = 0.25
                if sc == 6:
                    for i in range(m):
                        if st0[a + i] == 1:
                            keep[i] = 0.0
                for i in range(m):
                    pn[i] = labv[i] == 0 or (cells_on and cl[i] < 0)
                st = form_tilt(bb, labv, lam, u, grp, gcap, pn, keep, cl, cells_on, wr)
            # ρ 与固定
            gs = 0.0
            h2 = 0.0
            h15 = 0.0
            trf = 0.0
            ncap = 0
            capv = 0.0
            for i in range(m):
                base = bb[i] * keep[i]
                if sc <= 1:
                    rho[sc, a + i] = 1.0 if wr[i] > 0.0 else 0.0
                else:
                    rho[sc, a + i] = wr[i] / base if base > 0.0 else 0.0
                pin[sc, a + i] = pn[i]
                gs += wr[i]
                h2 += wr[i] * wr[i]
                h15 += wr[i] ** 1.5
                if wr[i] > bb[i]:
                    trf += wr[i] - bb[i]
                if wr[i] > 0.0 and wr[i] >= u[i] * (1.0 - 1e-12):
                    ncap += 1
                if wr[i] > u[i] and sc >= 2:
                    if wr[i] - u[i] > capv:
                        capv = wr[i] - u[i]
            gsum = np.zeros(G)
            for i in range(m):
                if grp[i] >= 0:
                    gsum[grp[i]] += wr[i]
            nind = 0
            nb = 0
            indv = 0.0
            for g in range(G):
                if gsum[g] > 0.0:
                    nind += 1
                    if gsum[g] >= gcap[g] * (1.0 - 1e-12):
                        nb += 1
                    if gsum[g] > gcap[g] and gsum[g] - gcap[g] > indv:
                        indv = gsum[g] - gcap[g]
            stats[sc, d, 0] = gs
            stats[sc, d, 1] = h2
            stats[sc, d, 2] = h15
            stats[sc, d, 3] = gs * gs / h2 if h2 > 0.0 else np.nan
            stats[sc, d, 4] = 1.0 / h2 if h2 > 0.0 else np.nan
            stats[sc, d, 5] = h15 / gs if gs > 0.0 else np.nan
            stats[sc, d, 6] = trf / gs if gs > 0.0 else np.nan
            stats[sc, d, 7] = ncap / m
            stats[sc, d, 8] = nb / nind if nind > 0 else 0.0
            stats[sc, d, 9] = st
            stats[sc, d, 10] = capv
            stats[sc, d, 11] = indv
    return 0


def flat_stats(ptr, w, T):
    """FLAT（源 DEV b）形成层逐日统计（同列定义）。"""
    st = np.full((T, NSTAT), np.nan)
    for d in range(T):
        a, b = ptr[d], ptr[d + 1]
        if b == a:
            continue
        x = w[a:b]
        g = x.sum()
        h2 = (x * x).sum()
        h15 = (x ** 1.5).sum()
        st[d] = (g, h2, h15, g * g / h2 if h2 > 0 else np.nan, 1 / h2 if h2 > 0 else np.nan, h15 / g if g > 0 else np.nan, 0.0,
                 float(np.mean(np.isclose(x, O.STOCK_CAP, rtol=0, atol=1e-15))), np.nan, 0, 0.0, 0.0)
    return st


def main():
    t0 = time.time()
    mk = A.Market()
    cd = mk.cd
    od = os.path.join(cd, 'overlay')
    os.makedirs(od, exist_ok=True)
    T = mk.T
    cvr20 = np.ascontiguousarray(np.asarray(mk.cvr20, np.float64))
    cvr5 = np.ascontiguousarray(np.asarray(mk.cvr5, np.float64))
    zsz = np.ascontiguousarray(np.asarray(mk.zsz, np.float64))
    lvl = np.ascontiguousarray(np.asarray(mk.lvl, np.int8))
    isk = np.ascontiguousarray(np.asarray(mk.iskid, np.int64))
    ind = np.ascontiguousarray(np.asarray(mk.ind, np.int64))
    facts = {}
    for f in O.FORMS:
        for m in O.MEMS:
            ptr, col, w = mk.formation(f, m)
            n = len(w)
            lab = {k: np.zeros(n, np.int8) for k in ('lab20', 'lab5', 'labsz', 'labcell')}
            why = {k: np.zeros(n, np.int8) for k in ('why20', 'why5', 'whysz', 'whycell')}
            st0 = np.zeros(n, np.int8)
            cell = np.zeros(n, np.int32)
            rho = np.zeros((8, n))
            pin = np.zeros((8, n), np.bool_)
            stats = np.full((8, T, NSTAT), np.nan)
            build(ptr, col, w, cvr20, cvr5, zsz, lvl, isk, ind, mk.capsh, O.IND_DEV, O.RESEARCH_CAP, T,
                  lab['lab20'], lab['lab5'], lab['labsz'], lab['labcell'], why['why20'], why['why5'], why['whysz'], why['whycell'], st0, cell, rho, pin, stats)
            arr = dict(lab, **why)
            arr.update(st0=st0, cell=cell, stats_FLAT=flat_stats(ptr, w, T))
            for i, sc in enumerate(SCHEMES):
                arr['rho|' + sc] = rho[i]
                arr['pin|' + sc] = pin[i]
                arr['stats|' + sc] = stats[i]
            O.atomic_write_npz(os.path.join(od, '%s|%s.npz' % (f, m)), **arr)
            fst = {}
            for i, sc in enumerate(SCHEMES):
                stt = stats[i]
                live = np.isfinite(stt[:, 0])
                fst[sc] = dict(days=int(live.sum()), status_nonzero_days=int((stt[live, 9] != 0).sum()), max_capviol=float(np.nanmax(stt[live, 10])) if live.any() else 0.0,
                               max_indviol=float(np.nanmax(stt[live, 11])) if live.any() else 0.0,
                               mean_transfer=float(np.nanmean(stt[live, 6])) if live.any() else np.nan,
                               rho_zero_share=float(np.mean(rho[i] == 0.0)) if n else 0.0)
            facts['%s|%s' % (f, m)] = dict(n=int(n), lab20=np.bincount(lab['lab20'], minlength=4).tolist(), why20=np.bincount(why['why20'], minlength=4).tolist(),
                                           st0=dict(bad=int((st0 == 1).sum()), good=int((st0 == 0).sum()), unknown=int((st0 < 0).sum())),
                                           cell_unknown=int((cell < 0).sum()), schemes=fst)
            O.log('overlay %s|%s：%d 项（%.0f s）' % (f, m, n, time.time() - t0))
    facts['wall_s'] = round(time.time() - t0, 1)
    facts['rss_peak_gb'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2)
    O.atomic_write_json(os.path.join(od, 'overlay_facts.json'), facts)
    bad = [k for k, v in facts.items() if isinstance(v, dict) and 'schemes' in v and any(s['status_nonzero_days'] for s in v['schemes'].values())]
    O.write_receipt('E6r_overlay', [os.path.join(od, 'overlay_facts.json')] + [os.path.join(od, '%s|%s.npz' % (f, m)) for f in O.FORMS for m in O.MEMS],
                    code=[__file__, KL.__file__, A.__file__, O.__file__], combos=18, projection_status_nonzero=bad)
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk != 'schemes'}) for k, v in list(facts.items())[:3]},
                     ensure_ascii=False), flush=True)
    print(json.dumps(dict(projection_status_nonzero=bad, wall_s=facts['wall_s']), ensure_ascii=False), flush=True)
    if bad:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
