# -*- coding: utf-8 -*-
"""E6m 阶段 S（B2 开发）· 合成账本：按 e6l / e6k_acct 账户格式（desc × 日 DESC_KEYS；目标 × 日 TGT_KEYS）为全部登记描述符生成确定性合成数，
供下游统计链（stats / cmpstats / MDE / 政策 / bootstrap / 分解 / 固定表）在没有真实收益的情况下打通与做闭合恒等测试。
**不是收益**：全部数由显式种子的伪随机数生成，标 SYNTHETIC；不读任何行情或收益。
构造（便于已知答案测试）：父 net8 = 段 × 形态 × H 的噪声；子 net8 = 父 + δ_config + 小噪声（δ 由配置哈希定，年化约 ±.5 百分点）；
gross = net8 + turn·8e−4；段首 19 日与 1% 随机日为 NaN（检验共同有限日逻辑）；父 sc_child = net8、sc_parent = NaN（同 E6l 父账户）。"""
import os
import sys
import json
import time
import argparse

import numpy as np
import pandas as pd

import e6m_core as M

DESC_KEYS = ('gross', 'pos', 'turn', 'net8', 'sc_child', 'sc_parent', 'bracket', 'qmiss', 'roll_zT', 'roll_unkT', 'roll_zL', 'roll_unkL')
TGT_KEYS = ('nnames', 'wsum', 'zT_mean', 'unkT', 'zL_mean', 'unkL', 'small30', 'szT_lo', 'szT_hi', 'szL_lo', 'szL_hi',
            'gapT', 'gapL', 'n_edits', 'n_in', 'n_out', 'edit_w_in', 'lv5')
FORMS = ('A4b', 'A4b_CVRv5', 'M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5', 'R2', 'A06')
SEGS = ('2010-2014', '2015-2018', '2019-2023', '2024-2026')


def out_dir(seg):
    return M.P('stageS_dev', 'synth', 'accounts', seg)


def seg_dates(seg):
    z = np.load(M.P('stageN', 'B3_prelim', 'work', 'masks_%s.npz' % seg), allow_pickle=False)
    return np.array([str(x) for x in z['date_ids']])


def config_id(desc_id):
    p = desc_id.split('|')
    return '|'.join(p[:6] + p[7:])


def delta_of(cid):
    return (M.stable_seed_int('E6m-synth-delta', cid) % 2001 - 1000) / 1000.0 * 2e-5


def build(seg, form, D):
    dates = seg_dates(seg)
    T = len(dates)
    rng = lambda *k: M.rng_for('E6m-synth', seg, form, *k)
    Df = D[D.parent == form].copy()
    Df['config_id'] = Df.desc_id.map(config_id)
    cids = sorted(set(Df.config_id))
    cpos = {c: j for j, c in enumerate(cids)}
    nanmask = np.zeros(T, bool)
    nanmask[:19] = True
    nanmask |= rng('nan').uniform(size=T) < 0.01
    par = {}
    for H in sorted(set(Df.H.astype(int))):
        x = rng('parent', H).normal(0.0, 1e-3, T)
        par[H] = np.where(nanmask, np.nan, x)
    DESC = {k: [] for k in DESC_KEYS}
    ids, tgt, Hs = [], [], []
    for r in Df.itertuples():
        H = int(r.H)
        is_par = r.operator == 'PARENT'
        if is_par:
            net = par[H]
        else:
            net = par[H] + delta_of(r.config_id) + rng('child', r.desc_id).normal(0.0, 2e-4, T)
        turn = np.abs(0.05 + rng('turn', r.desc_id).normal(0.0, 0.01, T))
        vals = dict(net8=net, gross=net + turn * 8e-4, turn=turn, pos=np.clip(0.9 + rng('pos', r.desc_id).normal(0, 0.02, T), 0, 1),
                    sc_child=net * 0.98 if not is_par else net, sc_parent=par[H] * 0.97 if not is_par else np.full(T, np.nan),
                    bracket=np.abs(rng('br', r.desc_id).normal(1e-5, 2e-6, T)), qmiss=np.zeros(T),
                    roll_zT=rng('rz', r.desc_id).uniform(0.3, 0.7, T), roll_unkT=np.full(T, 0.01), roll_zL=rng('rl', r.desc_id).uniform(0.3, 0.7, T),
                    roll_unkL=np.full(T, 0.01))
        for k in DESC_KEYS:
            v = vals[k]
            DESC[k].append(np.where(nanmask, np.nan, v) if k in ('net8', 'gross', 'sc_child', 'sc_parent') else v)
        ids.append(r.desc_id)
        tgt.append(cpos[r.config_id])
        Hs.append(H)
    S_ = M.read_csv_keep(M.P('registry', 'supplemental_E6m.csv'), dtype=str)
    for s in S_[S_.parent == form].itertuples():                    # 补充对象（SUPP:前 16 位；与 owner 同 H）
        H = int(s.H)
        sid = 'SUPP:' + s.supp_id[:16]
        net = par[H] + delta_of(sid) + rng('child', sid).normal(0.0, 2e-4, T)
        turn = np.abs(0.05 + rng('turn', sid).normal(0.0, 0.01, T))
        vals = dict(net8=net, gross=net + turn * 8e-4, turn=turn, pos=np.full(T, 0.9), sc_child=net * 0.98, sc_parent=par[H] * 0.97,
                    bracket=np.full(T, 1e-5), qmiss=np.zeros(T), roll_zT=np.full(T, 0.5), roll_unkT=np.full(T, 0.01), roll_zL=np.full(T, 0.5),
                    roll_unkL=np.full(T, 0.01))
        for k in DESC_KEYS:
            v = vals[k]
            DESC[k].append(np.where(nanmask, np.nan, v) if k in ('net8', 'gross', 'sc_child', 'sc_parent') else v)
        ids.append(sid)
        tgt.append(0)
        Hs.append(H)
    TS = {}
    g = rng('tgt')
    for k in TGT_KEYS:
        TS[k] = g.uniform(0.0, 1.0, (len(cids), T)) * (100.0 if k == 'nnames' else 1.0)
    p = os.path.join(out_dir(seg), '%s.npz' % form)
    os.makedirs(out_dir(seg), exist_ok=True)
    M.atomic_write_npz(p, desc=np.array(ids), desc_target=np.array(tgt), desc_H=np.array(Hs), targets=np.array(cids), dates=dates,
                       n_cells=np.array([0]), status=np.array(['SYNTHETIC']), **{'d_' + k: np.vstack(DESC[k]) for k in DESC_KEYS},
                       **{'t_' + k: TS[k] for k in TGT_KEYS})
    return p, len(ids)


def build_randoms(seg, P=64):
    """合成随机分片（E6l randoms 格式）：每个随机登记行（item 2–4，标准 owner）一行；路径日序列 = 合成父 net8 + 噪声（随机效应 0）。
    输出 stageS_dev/synth/randoms/<机制>/<段>/synth__p0_<P>.npz。"""
    A = M.read_csv_keep(M.P('registry', 'auxiliary_manifest_E6m.csv'), dtype=str)
    A = A[A.item.isin(['2', '3', '4']) & (A.owner_id.str.count(r'\|') >= 8) & (A.mechanism != 'NO_NEW_CONTENT_TO_PERMUTE')]
    dates = seg_dates(seg)
    T = len(dates)
    outs = []
    for mech, g in A.groupby('mechanism'):
        nr = len(g)
        s_net = np.zeros((nr, P))
        n_net = np.zeros((nr, P), np.int32)
        dsum = np.zeros((nr, T))
        dcnt = np.zeros((nr, T), np.int32)
        for i, r in enumerate(g.itertuples()):
            form = r.owner_id.split('|')[1]
            rng = M.rng_for('E6m-synth-rand', seg, mech, r.owner_id)
            base = M.rng_for('E6m-synth', seg, form, 'parent', int(r.H)).normal(0.0, 1e-3, T)
            X = base[None, :] + rng.normal(0.0, 2e-4, (P, T))
            X[:, :19] = np.nan
            fin = np.isfinite(X)
            s_net[i] = np.where(fin, X, 0.0).sum(1)
            n_net[i] = fin.sum(1)
            dsum[i] = np.where(fin, X, 0.0).sum(0)
            dcnt[i] = fin.sum(0)
        od = M.P('stageS_dev', 'synth', 'randoms', mech, seg)
        os.makedirs(od, exist_ok=True)
        p = os.path.join(od, 'synth__p0_%d.npz' % P)
        M.atomic_write_npz(p, desc=g.owner_id.values.astype(str), H=g.H.astype(int).values, path0=np.array([0]), n_paths=np.array([P]),
                           s_net=s_net, n_net=n_net, s_gross=s_net + 0.0, n_gross=n_net.copy(), s_turn=np.full((nr, P), 0.05 * T), s_pos=np.full((nr, P), 0.9 * T),
                           dsum=dsum, dsq=dsum * 0.0, dcnt=dcnt, dates=dates, status=np.array(['SYNTHETIC']))
        outs.append(p)
    return outs


def main():
    t0 = time.time()
    if len(sys.argv) > 1 and sys.argv[1] == 'randoms':
        outs = []
        for seg in SEGS:
            outs += build_randoms(seg)
        M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_synth_randoms'), outs, status='SUCCEEDED', code=[__file__, M.__file__], note='合成随机（SYNTHETIC）',
                        wall_s=round(time.time() - t0, 1))
        print(json.dumps(dict(files=len(outs), wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
        return 0
    D = M.read_csv_keep(M.P('registry', 'descriptors_E6m.csv'), dtype=str)
    rows = []
    outs = []
    for seg in SEGS:
        for form in FORMS:
            p, n = build(seg, form, D)
            outs.append(p)
            rows.append(dict(segment=seg, form=form, descriptors=n))
    df = pd.DataFrame(rows)
    p = M.P('stageS_dev', 'synth', 'synth_accounts_counts.csv')
    M.atomic_write_csv(p, df)
    M.write_receipt(os.environ.get('E6M_TASK', 'S_dev_synth_accounts'), [p] + outs, status='SUCCEEDED', code=[__file__, M.__file__],
                    note='合成账本（SYNTHETIC，非收益）', descriptors_total=int(df.descriptors.sum()), wall_s=round(time.time() - t0, 1))
    print(df.groupby('segment').descriptors.sum().to_string(), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
