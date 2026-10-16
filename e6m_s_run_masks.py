# -*- coding: utf-8 -*-
"""E6m 阶段 S · 名单阶段（brief §1.4 Stage A 之前的掩码层；plan §5 / §6 / §8.3）。不读任何收益、不算 DEV / 账本。

一个进程处理一个 (段, 父形态)：
- 登记描述符去掉 H → 门配置（H 只影响账本，不影响名单）；逐配置派发到 e6m_s_ops，得门 G → st.down → 最终名单；
- V_STATE 在父最终名单上后置删票。
输出 stageS_dev/masks/<段>/<形态>.npz：配置 ID、最终名单位图（packbits）、门位图；外加 facts_<形态>.csv（门 / 名单层事实）。
状态：C1 / M / S = SOURCE_WAIT（E6i 缓存，X03）；R2 / A06 = OUT_OF_SCOPE_MOCK；其余 COMPUTED。
B2 开发期 st = e6m_s_mock.MockStruct；阶段 S 换成真实 Struct，派发与输出格式不变。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import hashlib
import argparse
import resource

import numpy as np
import pandas as pd

import e6m_core as M
import e6m_s_ops as S
import e6m_s_meas as ME

WAIT_MEAS = ('C1', 'M', 'S')
OUT_PARENTS = ('R2', 'A06')
TWO = ('Q_MAX2', 'Q_MIN2', 'Q_LAGRAW1', 'Q_MEAN2')
TRENDC = {'UP': 2, 'DOWN': 0, 'MIXED': 1}


def fnum(x):
    return None if x in ('NOT_APPLICABLE', '-', '') else float(x)


def config_id(desc_id):
    p = desc_id.split('|')
    return '|'.join(p[:6] + p[7:])          # 去掉 H


def configs(form):
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    D = D[D.parent == form].copy()
    D['config_id'] = D.desc_id.map(config_id)
    keep = ['config_id', 'block', 'family', 'measurement', 'parent', 'operator', 'param', 'alpha', 'memory', 'adapter', 'condition', 'score_geometry']
    g = D.groupby('config_id')
    C = g.first()[keep[1:]].reset_index()
    C['n_desc'] = g.size().values
    C['H_list'] = g.H.agg(lambda s: '/'.join(sorted(s, key=int))).values
    return C


class Runner(object):
    def __init__(self, seg_name, form, struct='mock', seg=None):
        import e6m_s_real as RL
        self.struct = struct
        self.seg = seg if seg is not None else RL.seg_of(seg_name, struct)
        self.st = self.seg.struct(form)
        self.form = form
        me = ME.load(seg_name)
        if not (np.array_equal(me['t'], self.seg.ci.t) and np.array_equal(me['c'], self.seg.ci.c)):
            raise RuntimeError('测量单元坐标与段结构不一致（%s）' % struct)
        self.me = me
        self.kf = RL.kfs_of(self.seg, struct, me)
        self.mem_gate = RL.mem_gate_of(struct)
        self.mem_gate_s = RL.mem_gate_s_of(struct)
        self.wait = RL.wait_meas(struct)
        self._ctx = {}
        self._memo = {}
        self._down = {}
        self.ctx0 = self.ctx('Q0')
        self.F0 = self.down(self.ctx0.U0)

    def ctx(self, meas):
        if meas not in self._ctx:
            self._ctx[meas] = S.Ctx(self.st, self.kf[meas], mem_gate=self.mem_gate, mem_gate_s=self.mem_gate_s)
        return self._ctx[meas]

    def down(self, G):
        h = hashlib.sha1(np.packbits(G).tobytes()).hexdigest()
        if h not in self._down:
            self._down[h] = self.st.down(G[None, :])[0]
        return self._down[h]

    def memo(self, key, fn):
        if key not in self._memo:
            self._memo[key] = fn()
        return self._memo[key]

    # ---------------------------------------------------------------- V_STATE（plan §8.3）
    def v_tails(self, d):
        """经济 V（vol ≥ 0）→ pool0 源中性化 → 源 qcut k = 1/d 组：最高组 = 高尾、最低组 = 低尾；只取有值格（V 无效不删）。"""
        def f():
            import comprehensive_factor_diagnosis as C
            seg = self.seg
            ctx = seg.ctx
            pool0 = ctx['pool0']
            dense = np.full(pool0.shape, np.nan)
            dense[seg.ci.t, seg.ccols[seg.ci.c]] = self.me['vol']
            neu = C.precompute_neutralized_factor(pd.DataFrame(dense, index=pool0.index, columns=pool0.columns), pool0, ctx['log_mcap'])
            k = int(round(1.0 / d))
            valued = np.zeros(pool0.shape, bool)
            di = {x: i for i, x in enumerate(pool0.index)}
            cp = {x: j for j, x in enumerate(pool0.columns)}
            for day, s in neu.items():
                s = s.dropna()
                valued[di[day], [cp[x] for x in s.index]] = True
            kh = C.build_factor_strategy_holdings_cached(neu, pool0, k, [k]).to_numpy() == 1
            kl = C.build_factor_strategy_holdings_cached(neu, pool0, k, [1]).to_numpy() == 1
            return dict(HIGH=seg.cells(valued & ~kh), LOW=seg.cells(valued & ~kl))
        return self.memo(('vtail', d), f)

    def v_state(self, cfg):
        d = fnum(cfg['param'])
        tail = self.v_tails(d)['HIGH' if cfg['operator'] == 'DELETE_HIGH' else 'LOW']
        tr = self.me['trend']
        cond = cfg['condition']
        if cond == 'ALL':
            elig = np.ones(len(tr), bool)
        elif cond == 'ALL_KNOWN':
            elig = tr >= 0
        elif cond == 'DOWN_MIXED':
            elig = (tr == TRENDC['DOWN']) | (tr == TRENDC['MIXED'])
        elif cond == 'UP':
            elig = tr == TRENDC['UP']
        else:
            raise ValueError(cond)
        dele = self.F0 & tail & elig
        return self.F0 & ~dele, dict(deleted=int(dele.sum()), tail_in_parent=int((self.F0 & tail).sum()))

    # ---------------------------------------------------------------- 派发
    def gate(self, cfg):
        blk, op, meas, mem = cfg['block'], cfg['operator'], cfg['measurement'], cfg['memory']
        p, a = fnum(cfg['param']), fnum(cfg['alpha'])
        if blk == 'PARENT':
            return self.ctx0.U0, {}
        if blk == 'OLD_RULE':
            return self.memo(('old', mem), lambda: S.source_gate(S._OldCtx(self.ctx0), 0.0, mem))
        c = self.ctx(meas)
        if blk in ('SOURCE', 'TWO_DAY'):
            g, f = self.memo(('src', meas, a, mem), lambda: S.source_gate(c, a, mem))
            if blk == 'TWO_DAY':
                f = dict(f, two_day_missing_dom=int((~np.isfinite(c.kq)).sum()))
            return g, f
        if blk in ('BAND_Q', 'LEAK_BRIDGE'):
            m = 'UNPROTECTED_LAG10' if mem == 'UNPROTECTED_LAG10' else 'PROTECTED_LAG10'
            gn, gm, f = self.memo(('band', meas, p, None, m), lambda: S.band_gates(c, p, None, m))
            return (gn, f['nomem']) if mem == 'NONE' else (gm, f['mem'])
        if blk == 'BAND_BLEND':
            gn, gm, f = self.memo(('band', meas, p, a, 'PROTECTED_LAG10'), lambda: S.band_gates(c, p, a, 'PROTECTED_LAG10'))
            return (gn, f['nomem']) if mem == 'NONE' else (gm, f['mem'])
        if blk == 'FILTER' and op == 'PRIORITY_PASS':
            gn, gm, f = self.memo(('prio', meas, p), lambda: S.priority_gates(c, p, 'RULE_LAG10'))
            return (gn, f['nomem']) if mem == 'NONE' else (gm, f['mem'])
        if blk == 'FILTER' and op == 'HARD_CONJ':
            return self.memo(('hard', meas, p, mem), lambda: S.hard_gates(c, p, mem))
        if blk == 'EDIT_MATCH':
            r, f = self.memo(('edit', meas, a, p), lambda: S.edit_gates(c, a, p))
            return r[op.replace('EDIT_', '')], f
        if blk == 'MEAN_SLOT_BRIDGE':
            return self.memo(('slot', meas, p, op), lambda: S.slot_bridge_gate(c, p, op))
        raise ValueError('未登记的配置：%s' % cfg['config_id'])

    def run(self):
        C = configs(self.form)
        rows, finals, gates, ids, has_gate = [], [], [], [], []
        n_dom = len(self.st.ids)
        for cfg in C.to_dict('records'):
            t1 = time.time()
            base = dict(config_id=cfg['config_id'], block=cfg['block'], operator=cfg['operator'], measurement=cfg['measurement'],
                        param=cfg['param'], alpha=cfg['alpha'], memory=cfg['memory'], adapter=cfg['adapter'], condition=cfg['condition'],
                        n_desc=cfg['n_desc'])
            if cfg['measurement'] in self.wait:
                rows.append(dict(base, status='SOURCE_WAIT'))
                continue
            if cfg['block'] == 'V_STATE':
                F, f = self.v_state(cfg)
                G = None
            else:
                G, f = self.gate(cfg)
                F = self.down(G)
            ids.append(cfg['config_id'])
            finals.append(np.packbits(F))
            gates.append(np.packbits(G) if G is not None else np.zeros_like(np.packbits(self.ctx0.U0)))
            has_gate.append(G is not None)
            row = dict(base, status='COMPUTED', final_members=int(F.sum()), final_vs_parent=int((F != self.F0).sum()),
                       final_added=int((F & ~self.F0).sum()), final_removed=int((~F & self.F0).sum()), seconds=round(time.time() - t1, 2))
            if G is not None:
                row.update(gate_members=int(G.sum()), gate_vs_U0=int((G != self.ctx0.U0).sum()))
            for k, v in (f or {}).items():
                row['f_' + k] = v
            rows.append(row)
        return C, pd.DataFrame(rows), ids, finals, gates, has_gate, n_dom


def main():
    import e6m_s_real as RL
    ap = argparse.ArgumentParser()
    ap.add_argument('--seg', required=True)
    ap.add_argument('--form', required=True)
    ap.add_argument('--struct', default='mock', choices=['mock', 'real'])
    a = ap.parse_args()
    t0 = time.time()
    tdef = ('S_dev_masks_%s_%s' if a.struct == 'mock' else 'S_masks_%s_%s') % (a.seg, a.form)
    if a.form in RL.out_parents(a.struct):
        C = configs(a.form)
        df = pd.DataFrame([dict(config_id=c, status='OUT_OF_SCOPE_MOCK', n_desc=n) for c, n in zip(C.config_id, C.n_desc)])
        p = RL.root(a.struct, 'masks', a.seg, 'facts_%s.csv' % a.form)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        M.atomic_write_csv(p, df)
        M.write_receipt(os.environ.get('E6M_TASK', tdef), [p], status='SUCCEEDED', code=[__file__, M.__file__])
        print(json.dumps(dict(seg=a.seg, form=a.form, configs=len(df), status='OUT_OF_SCOPE_MOCK'), ensure_ascii=False))
        return 0
    R = Runner(a.seg, a.form, a.struct)
    C, df, ids, finals, gates, has_gate, n_dom = R.run()
    od = RL.root(a.struct, 'masks', a.seg)
    os.makedirs(od, exist_ok=True)
    p1 = os.path.join(od, 'facts_%s.csv' % a.form)
    p2 = os.path.join(od, '%s.npz' % a.form)
    M.atomic_write_csv(p1, df)
    M.atomic_write_npz(p2, config_ids=np.array(ids), final_bits=np.array(finals), n_cells=np.array([R.seg.n]),
                       gate_bits=np.array(gates), has_gate=np.array(has_gate), n_dom=np.array([n_dom]),
                       parent_final_bits=np.packbits(R.F0), status=np.array(['ANCHOR_PENDING' if a.struct == 'mock' else 'REAL_STRUCT']))
    st = df.status.value_counts().to_dict()
    T = dict(configs=len(df), status_counts=st, downs_cached=len(R._down), wall_s=round(time.time() - t0, 1), struct=a.struct,
             rss_peak_gb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2, 2))
    M.write_receipt(os.environ.get('E6M_TASK', tdef), [p1, p2], status='SUCCEEDED', code=[__file__, S.__file__, M.__file__],
                    note='名单层（不读收益）：%s' % ('B2 开发 mock' if a.struct == 'mock' else '阶段 S 真实结构'), **T)
    print(json.dumps(dict(seg=a.seg, form=a.form, **T), ensure_ascii=False), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
