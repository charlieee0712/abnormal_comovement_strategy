# -*- coding: utf-8 -*-
"""E6k 账户与日聚合账本（brief W10；plan §4.2 / §9.2 / §12）。
目标（形成日 DEV 权重）与 H 无关：一个目标算一次，H 列表走 E6i 稀疏引擎（e6i_sparse.SparseEngine，与源 DEV 逐位、账本 ≤ 1e−12）。
描述符级（目标 × H）日数组：gross / pos / turn / net8（8bp，源 compute_calendar_pnl 口径）/ sc_child / sc_parent（MATCH-CAP：形成日双方只向较低
  资本缩减后各自完整账户）/ bracket（源 E6g 平方根冲击括号：Σ|q|^1.5 σ20/√ADV20，c = κ√A·bracket）/ qmiss（缺 ADV / σ 的交易额）/
  roll_zT / roll_unkT / roll_zL / roll_unkL（滚动持仓 act[d] 在 d 日 z 上的已知部分均值与未知份额）
目标级日数组：nnames / wsum / zT_mean / unkT / zL_mean / unkL（目标权重的已知 size 均值与未知份额）/ small30（z_T ≤ .3 份额）/
  szT_lo / szT_hi / szL_lo / szL_hi（相对父的组合层 size 差 ×100 的共同未知紧区间，plan §9.2）/ gapT / gapL（编辑层：换入中位 − 换出中位，
  两边都有且 size 已知的日子）/ n_edits / n_in / n_out / edit_w_in（换入者目标权重份额）/ lv5（z_T 五分组当"行业"的最大超配，源 DEV 未归一）"""
import numpy as np

import e6k_env as E

DESC_KEYS = ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss', 'roll_zT', 'roll_unkT', 'roll_zL', 'roll_unkL')
TGT_KEYS = ('nnames', 'wsum', 'zT_mean', 'unkT', 'zL_mean', 'unkL', 'small30', 'szT_lo', 'szT_hi', 'szL_lo', 'szL_hi',
            'gapT', 'gapL', 'n_edits', 'n_in', 'n_out', 'edit_w_in', 'lv5')


class Acct(object):
    def __init__(self, seg, impact=True):
        self.seg = seg
        self.SE = seg.SE
        self.T = seg.T
        self.impact = impact
        if impact:
            import e6g_c as GC
            self.GC = GC
            self.mkt = GC.MarketCtx(seg.S)
        self.b5 = E.size_bins(seg.zc, 5)                  # (T, Nc)

    # ------------------------------------------------------------ 目标
    def target(self, kept):
        ids = np.flatnonzero(kept)
        ci = self.seg.ci
        t, c = ci.t[ids], ci.c[ids]
        w = self.SE.dev(t, c)
        return dict(ids=ids, t=t, c=c, w=w)

    def wcell(self, tg):
        out = np.zeros(self.seg.n)
        out[tg['ids']] = tg['w']
        return out

    # ------------------------------------------------------------ 描述符级
    def ledgers(self, tg, Hs, par=None, impact=None, roll=True):
        SE, T = self.SE, self.T
        t, c, w = tg['t'], tg['c'], tg['w']
        Hs = tuple(sorted(set(int(h) for h in Hs)))
        led = SE.pnl(t, c, w, Hs, 8.0)
        out = {H: dict(gross=led[H][0], pos=led[H][1], turn=led[H][2], net8=led[H][3]) for H in Hs}
        if par is not None:
            tb, cb, wb = par['t'], par['c'], par['w']
            pc = np.bincount(t, weights=w, minlength=T)
            pb = np.bincount(tb, weights=wb, minlength=T)
            ps = np.minimum(pc, pb)
            with np.errstate(divide='ignore', invalid='ignore'):
                fc = np.where(pc > 0, ps / pc, 0.0)
                fb = np.where(pb > 0, ps / pb, 0.0)
            scc = SE.pnl(t, c, w * fc[t], Hs, 8.0)
            scb = SE.pnl(tb, cb, wb * fb[tb], Hs, 8.0)
            for H in Hs:
                out[H]['sc_child'] = scc[H][3]
                out[H]['sc_parent'] = scb[H][3]
        else:
            for H in Hs:
                out[H]['sc_child'] = out[H]['net8']
                out[H]['sc_parent'] = np.full(T, np.nan)
        if (self.impact if impact is None else impact):
            order = np.argsort(t, kind='stable')
            ts = t[order]
            bnd = np.searchsorted(ts, np.arange(T + 1))
            idx = [c[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
            val = [w[order[bnd[d]:bnd[d + 1]]] for d in range(T)]
            for H in Hs:
                br = self.GC.profile_and_impact(self.mkt, idx, val, H, full_profile=False)
                out[H]['bracket'] = br[0]['sqrt']
                out[H]['qmiss'] = br[3]
        else:
            for H in Hs:
                out[H]['bracket'] = np.full(T, np.nan)
                out[H]['qmiss'] = np.full(T, np.nan)
        if roll:
            rz = self.roll_expo(t, c, w, Hs)
            for H in Hs:
                out[H].update(rz[H])
        else:
            for H in Hs:
                for k in ('roll_zT', 'roll_unkT', 'roll_zL', 'roll_unkL'):
                    out[H][k] = np.full(T, np.nan)
        return out

    def roll_expo(self, t, c, w, Hs):
        """act[d] = 最近 H 个形成日目标权重之和 / den（den 在比值里约去）；用 d 日 z_T / z_LAG1 估值。"""
        T = self.T
        seg = self.seg
        Hmax = max(Hs)
        if len(t) == 0:
            return {H: dict(roll_zT=np.full(T, np.nan), roll_unkT=np.full(T, np.nan), roll_zL=np.full(T, np.nan),
                            roll_unkL=np.full(T, np.nan)) for H in Hs}
        ks = np.arange(Hmax)
        tt = t[:, None] + ks[None, :]
        ok = tt < T
        ttc = np.minimum(tt, T - 1)
        zT = seg.zc[ttc, c[:, None]]
        zL = seg.zLc[ttc, c[:, None]]
        W = np.broadcast_to(w[:, None], tt.shape)
        li = np.broadcast_to(ks[None, :], tt.shape)
        key = (li * T + tt)[ok]

        def acc(v):
            return np.cumsum(np.bincount(key, weights=v[ok], minlength=Hmax * T).reshape(Hmax, T), axis=0)
        tot = acc(W)
        kT, kL = np.isfinite(zT), np.isfinite(zL)
        nT, uT = acc(np.where(kT, W * np.where(kT, zT, 0.0), 0.0)), acc(np.where(kT, 0.0, W))
        nL, uL = acc(np.where(kL, W * np.where(kL, zL, 0.0), 0.0)), acc(np.where(kL, 0.0, W))
        out = {}
        with np.errstate(divide='ignore', invalid='ignore'):
            for H in Hs:
                i = H - 1
                out[H] = dict(roll_zT=np.where(tot[i] - uT[i] > 0, nT[i] / (tot[i] - uT[i]), np.nan),
                              roll_unkT=np.where(tot[i] > 0, uT[i] / tot[i], np.nan),
                              roll_zL=np.where(tot[i] - uL[i] > 0, nL[i] / (tot[i] - uL[i]), np.nan),
                              roll_unkL=np.where(tot[i] > 0, uL[i] / tot[i], np.nan))
        return out

    # ------------------------------------------------------------ 目标级
    def target_stats(self, tg, kept, par_kept=None, par_tg=None):
        seg, T = self.seg, self.T
        ci = seg.ci
        t, c, w, ids = tg['t'], tg['c'], tg['w'], tg['ids']
        o = {}
        o['nnames'] = np.bincount(t, minlength=T).astype(float)
        P_ = np.bincount(t, weights=w, minlength=T)
        o['wsum'] = P_
        zT, zL = seg.zT[ids], seg.zL[ids]
        with np.errstate(divide='ignore', invalid='ignore'):
            for nm, z in (('T', zT), ('L', zL)):
                kn = np.isfinite(z)
                num = np.bincount(t[kn], weights=w[kn] * z[kn], minlength=T)
                unk = np.bincount(t[~kn], weights=w[~kn], minlength=T)
                o['z%s_mean' % nm] = np.where(P_ - unk > 0, num / (P_ - unk), np.nan)
                o['unk%s' % nm] = np.where(P_ > 0, unk / P_, np.nan)
            s30 = np.isfinite(zT) & (zT <= 0.3)
            o['small30'] = np.where(P_ > 0, np.bincount(t[s30], weights=w[s30], minlength=T) / P_, np.nan)
        # 源 DEV 口径的 size 五分组超配（未归一）
        b = self.b5[t, c]
        dev = np.full((T, 5), 0.0)
        kb = b >= 0
        np.add.at(dev, (t[kb], b[kb]), w[kb])
        lv = dev - seg.share5
        o['lv5'] = np.where(P_ > 0, lv.max(axis=1), np.nan)
        if par_kept is not None:
            wc = self.wcell(tg)
            wb = self.wcell(par_tg)
            Pb = np.bincount(par_tg['t'], weights=par_tg['w'], minlength=T)
            both = (P_ > 0) & (Pb > 0)
            with np.errstate(divide='ignore', invalid='ignore'):
                a = np.where(both[ci.t], wc / np.where(P_ > 0, P_, 1)[ci.t] - wb / np.where(Pb > 0, Pb, 1)[ci.t], 0.0)
            for nm, z in (('T', seg.zT), ('L', seg.zL)):
                kn = np.isfinite(z)
                k_ = np.bincount(ci.t, weights=np.where(kn, a * np.where(kn, z, 0.0), 0.0), minlength=T)
                lo = k_ + np.bincount(ci.t, weights=np.where(~kn, np.minimum(a, 0.0), 0.0), minlength=T)
                hi = k_ + np.bincount(ci.t, weights=np.where(~kn, np.maximum(a, 0.0), 0.0), minlength=T)
                o['sz%s_lo' % nm] = np.where(both, 100.0 * lo, np.nan)
                o['sz%s_hi' % nm] = np.where(both, 100.0 * hi, np.nan)
            ent = kept & ~par_kept
            ext = par_kept & ~kept
            o['n_in'] = np.bincount(ci.t[ent], minlength=T).astype(float)
            o['n_out'] = np.bincount(ci.t[ext], minlength=T).astype(float)
            o['n_edits'] = o['n_in'] + o['n_out']
            with np.errstate(divide='ignore', invalid='ignore'):
                o['edit_w_in'] = np.where(P_ > 0, np.bincount(ci.t, weights=np.where(ent, wc, 0.0), minlength=T) / P_, np.nan)
            for nm, z in (('T', seg.zT), ('L', seg.zL)):
                o['gap%s' % nm] = edit_gap(seg, ent, ext, z)
        else:
            for k in ('szT_lo', 'szT_hi', 'szL_lo', 'szL_hi', 'gapT', 'gapL', 'n_edits', 'n_in', 'n_out', 'edit_w_in'):
                o[k] = np.full(T, np.nan)
        return o


def edit_gap(seg, ent, ext, z):
    """E6j e6j_run_p.size_gap 的逐日量：换入 z 中位 − 换出 z 中位（两边都有且 z 已知的日子，否则 NaN）。"""
    T = seg.T
    out = np.full(T, np.nan)
    ci = seg.ci
    for d in np.unique(ci.t[ent | ext]):
        a0, a1 = seg.off[d], seg.off[d + 1]
        e = z[a0:a1][ent[a0:a1]]
        x = z[a0:a1][ext[a0:a1]]
        e = e[np.isfinite(e)]
        x = x[np.isfinite(x)]
        if len(e) and len(x):
            out[d] = np.median(e) - np.median(x)
    return out
