# -*- coding: utf-8 -*-
"""E6j 随机层分段计时（只测时，不写任何结果文件、不写回执）：P 随机的每条路径 × α 拆成
draw（u_cells / assign_by_priority）/ blend / kept（第一关 KeepDom.keep / 第二关 dep_stage2_keep / 其余）/ dev / pnl，
EDIT 类另计 edit_masks。用法：--segment --form --arm --paths --mechs IID,EDIT"""
import e6j_boot  # noqa: F401
import sys
import time
import json

import numpy as np

import e6j_engine as EN
import e6j_slot as SL
import e6j_random as RND
import e6j_run_prand as RR
import e6i_randoms as IR

acc = {}


def tick(k, t0):
    acc[k] = acc.get(k, 0.0) + (time.perf_counter() - t0)


# 包一层计时（不改行为）
_u, _a, _keep, _s2 = RND.Grid.u_cells, RND.assign_by_priority, IR.KeepDom.keep, IR.dep_stage2_keep


def u_cells(self, *a, **k):
    t0 = time.perf_counter(); r = _u(self, *a, **k); tick('draw.u_cells', t0); return r


def assign(*a, **k):
    t0 = time.perf_counter(); r = _a(*a, **k); tick('draw.assign_lexsort', t0); return r


def keep(self, *a, **k):
    t0 = time.perf_counter(); r = _keep(self, *a, **k); tick('kept.KeepDom_keep', t0); return r


def s2(*a, **k):
    t0 = time.perf_counter(); r = _s2(*a, **k); tick('kept.stage2_T', t0); return r


RND.Grid.u_cells, RND.assign_by_priority, IR.KeepDom.keep, IR.dep_stage2_keep = u_cells, assign, keep, s2
EN.IR.dep_stage2_keep = s2


def main():
    a = sys.argv
    seg, form, arm = a[a.index('--segment') + 1], a[a.index('--form') + 1], a[a.index('--arm') + 1]
    n = int(a[a.index('--paths') + 1]); mechs = a[a.index('--mechs') + 1].split(',')
    t0 = time.perf_counter()
    env = EN.Env(seg, with_prod=True)
    ctx, ci, SE = env.ctx, env.ci, env.SE
    names = [m for _, m in RR.ARMS[arm]]
    comps = {k: env._dense_cells(SL.member_pct(ctx, *RR.COMP[k])[0]) for k in names}
    st = EN.prod_structure(env, form)
    perm = RR.Perm(env, comps, env.pK)
    legal = ~env.cvr if form.endswith('_CVRv5') else np.ones(ci.n, bool)
    parent = st.kept(st.q0[None, :])[0]
    real = {x: st.kept(EN.blend(st.q0, [(sh, comps[m][None, :]) for sh, m in RR.ARMS[arm]], x))[0] for x in RR.ALPHAS}
    tick('setup(env+structures)', t0)
    acc.clear(); acc['setup_s'] = time.perf_counter() - t0
    info = dict(segment=seg, form=form, arm=arm, paths=n, n_cells=int(ci.n), T=int(ci.T), valid_new=int(np.isfinite(comps[names[0]]).sum()))
    for mech in mechs:
        tm = time.perf_counter()
        for x in RR.ALPHAS:
            if mech.startswith('EDIT'):
                t1 = time.perf_counter()
                K = np.vstack([RR.edit_masks(env, parent, real[x], legal, env.pK, mech, p, form)[None, :] for p in range(n)])
                tick('%s.edit_masks' % mech, t1)
            else:
                Q = []
                for p in range(n):
                    t1 = time.perf_counter(); dv = perm.draw(mech, p); tick('%s.draw_total' % mech, t1)
                    t1 = time.perf_counter(); Q.append(EN.blend(st.q0, [(sh, dv[m][None, :]) for sh, m in RR.ARMS[arm]], x)[0]); tick('%s.blend' % mech, t1)
                t1 = time.perf_counter(); K = st.kept(np.vstack([q[None, :] for q in Q])); tick('%s.kept_total' % mech, t1)
            for j in range(n):
                kj = K[j]; t_, c_ = ci.t[kj], ci.c[kj]
                t1 = time.perf_counter(); w = SE.dev(t_, c_); tick('%s.dev' % mech, t1)
                t1 = time.perf_counter(); SE.pnl(t_, c_, w, RR.HS, 8.0); tick('%s.pnl' % mech, t1)
        acc['%s.wall' % mech] = time.perf_counter() - tm
    per = {k: (v / (n * len(RR.ALPHAS)) if not k.endswith(('wall', 'setup_s')) else v) for k, v in acc.items()}
    print(json.dumps(dict(info=info, seconds_total=acc, seconds_per_path_alpha=per), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
