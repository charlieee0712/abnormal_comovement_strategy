# -*- coding: utf-8 -*-
"""E6k Stage 0 第 6 类：输出 / 资源（brief §2 第 6 类；附录 A6-1 … A6-6、A3-12）。
对象 = profile 试跑产物（临时目录；新测量为当日内置换内容，无真实新信息）——只核机械合同，不读任何登记对象的收益：
  A6-1 profile：确定性任务（RP / HG / LX / CORE 所在任务）与随机任务（64 路径）的 wall / RSS / 分段秒数 → stage0/profile.csv
  A6-2 日账本 schema：描述符级 12 列、目标级 18 列齐；位图长度 = pool0 单元数（按 packbits 字节数核）
  A6-3 费用恒等：抽 500 个描述符，逐日 net8 = gross − 8e−4·turn（≤ 1e−15 量级浮点）；8bp − 6bp = −2e−4·turn 由同一式推出（6bp 只作 E5a 对账）
  A3-12 权重可确定性重算：抽 200 个目标，由位图 → DEV → 稀疏账本重算 wsum / nnames 与首个 H 的 net8，= 已存（≤ 1e−12）
  A6-4 plan §16.3 脚本 103 / 103（已在 stage0/plan_tests；此处读回执）；A6-5 A0 逐元组（读 a0 清单）
  A6-6 query_id 跨文件唯一；每张卡 queries 非空；卡片行号与 PLAN_COPY 原文对得上"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_acct as AC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rerun', action='store_true')
    ap.add_argument('--reg', default=None)
    a = ap.parse_args()
    out = K.P('stage0', 'c6_output' + ('_rerun' if a.rerun else ''))
    os.makedirs(out, exist_ok=True)
    reg = a.reg or os.path.join(K.TRIAL, 'a0', 'registry')
    rows = []

    def chk(cid, what, ok, detail=''):
        rows.append(dict(check_id=cid, what=what, status='INFO' if ok is None else ('PASS' if ok else 'FAIL'), detail=str(detail)[:400]))
    # ---------------- A6-1
    prof = []
    for f in sorted(glob.glob(os.path.join(K.TRIAL, 'profile_det', '*', 'profile_*.csv'))):
        p = pd.read_csv(f)
        prof.append(dict(kind='deterministic', task=os.path.basename(f)[8:-4], n_targets=len(p), op_s=round(p.op_s.sum(), 1),
                         acct_s=round(p.acct_s.sum(), 1), max_op_s=round(p.op_s.max(), 2)))
    for f in sorted(glob.glob(os.path.join(K.TRIAL, 'logs', 'prof_det_*.log')) + glob.glob(os.path.join(K.TRIAL, 'logs', 'prof_rand_*.log'))):
        txt = [l for l in open(f, encoding='utf-8', errors='replace') if 'wall' in l and ('描述符' in l or '行；' in l)]
        if txt:
            prof.append(dict(kind='log', task=os.path.basename(f)[:-4], line=txt[-1].strip()))
    pp = os.path.join(out, 'profile.csv')
    K.atomic_write_csv(pp, pd.DataFrame(prof))
    chk('A6-1', 'profile：确定性与随机代表任务（stage0/c6_output/profile.csv）', None, '%d 行' % len(prof))
    # ---------------- A6-2 / A6-3 / A3-12
    files = sorted(glob.glob(os.path.join(K.TRIAL, 'profile_det', '*', '*.npz')))
    files = [f for f in files if not os.path.basename(f).startswith('weights_')]
    rng = np.random.default_rng(K.stable_seed_int('E6k.stage0.c6') % (2 ** 63))
    import e6k_env as E
    seg_cache = {}
    n_fee = 0
    worst_fee = 0.0
    n_rec = 0
    worst_rec = 0.0
    schema_ok = True
    for f in files:
        z = np.load(f, allow_pickle=False)
        need = ['d_' + k for k in AC.DESC_KEYS] + ['t_' + k for k in AC.TGT_KEYS] + ['bits', 'desc', 'desc_target', 'desc_H', 'targets', 'n_cells']
        miss = [k for k in need if k not in z.files]
        n = int(z['n_cells'][0])
        bits_ok = z['bits'].shape[1] == (n + 7) // 8
        schema_ok &= (not miss) and bits_ok
        chk('A6-2', '%s：schema（描述符 12 + 目标 18 列）与位图长度' % os.path.basename(f), (not miss) and bits_ok, 'missing=%s' % miss)
        nd = len(z['desc'])
        pick = rng.choice(nd, size=min(nd, 125), replace=False)
        g, tu, n8 = z['d_gross'][pick], z['d_turn'][pick], z['d_net8'][pick]
        r = n8 - (g - 8e-4 * tu)
        m = np.isfinite(r)
        worst_fee = max(worst_fee, float(np.max(np.abs(r[m]))) if m.any() else 0.0)
        n_fee += len(pick)
        pname = os.path.basename(os.path.dirname(f))
        if pname not in seg_cache:
            seg_cache[pname] = E.Seg(pname)
        seg = seg_cache[pname]
        tg_pick = rng.choice(len(z['targets']), size=min(len(z['targets']), 50), replace=False)
        for j in tg_pick:
            kept = np.unpackbits(z['bits'][j])[:n].astype(bool)
            ids = np.flatnonzero(kept)
            t, c = seg.ci.t[ids], seg.ci.c[ids]
            w = seg.SE.dev(t, c)
            ws = np.bincount(t, weights=w, minlength=seg.T)
            d1 = float(np.max(np.abs(ws - z['t_wsum'][j])))
            d2 = float(np.max(np.abs(np.bincount(t, minlength=seg.T) - z['t_nnames'][j])))
            di = np.flatnonzero(z['desc_target'] == j)
            if len(di):
                H = int(z['desc_H'][di[0]])
                n8 = seg.SE.pnl(t, c, w, (H,), 8.0)[H][3]
                ref = z['d_net8'][di[0]]
                mm = np.isfinite(ref) & np.isfinite(n8)
                d3 = float(np.max(np.abs(n8[mm] - ref[mm]))) if mm.any() else 0.0
                d3 += 0.0 if np.array_equal(np.isfinite(ref), np.isfinite(n8)) else 1.0
            else:
                d3 = 0.0
            worst_rec = max(worst_rec, d1, d2, d3)
            n_rec += 1
    chk('A6-3', '费用恒等 net8 = gross − 8e−4·turn（抽 %d 个描述符，逐日）' % n_fee, worst_fee <= 1e-15, 'max|resid| = %.2e' % worst_fee)
    chk('A3-12', '由位图 + DEV 输入重算 wsum / nnames / 首个 H 的 net8 = 已存（抽 %d 个目标）' % n_rec, worst_rec <= 1e-12,
        'max|Δ| = %.2e' % worst_rec)
    # ---------------- A6-4 / A6-5
    tr = json.load(open(K.P('stage0', 'plan_tests', 'out', 'test_results.json'), encoding='utf-8'))
    chk('A6-4', 'plan §16.3 脚本（sha %s）在 47 环境 %d / %d' % (tr['script_sha256'][:8], tr['passed'], tr['total']),
        tr['passed'] == tr['total'] == 103 and tr['script_sha256'].startswith('ebc9d4eb'))
    a0 = os.path.join(os.path.dirname(reg), 'a0_manifest_E6k.json') if 'e6k_trial' in reg else K.P('registration', 'a0_manifest_E6k.json')
    man = json.load(open(a0, encoding='utf-8'))
    chk('A6-5', 'A0：39,142 / 段 + 72 附属；独立枚举与规范脚本逐元组 / 块集合相等；144 主展示唯一存在',
        man['compare']['ok'] and man['counts']['raw_id_count'] == 39142 and man['counts']['accessory_INC'] == 72 and man['counts']['primary144'] == 144,
        json.dumps(man['compare'], ensure_ascii=False))
    # ---------------- A6-6
    qy = pd.read_csv(os.path.join(reg, 'query_registry_E6k.csv'))
    cards = pd.read_csv(os.path.join(reg, 'cards_E6k.csv'))
    chk('A6-6', 'query_id 唯一（%d 条）' % len(qy), qy.query_id.is_unique)
    chk('A6-6', '18 张卡每张 queries 非空且与注册表一致', len(cards) == 18 and all(
        len(str(q).split('|')) >= 1 and set(str(q).split('|')) <= set(qy.query_id) for q in cards.queries))
    plan = open(K.P('PLAN_COPY.md'), encoding='utf-8').read().split('\n')
    chk('A6-6', '卡片标题行号与 PLAN_COPY 原文逐行相同', all(plan[int(r.plan_line) - 1].replace('### ', '') == r.title for r in cards.itertuples()))
    df = pd.DataFrame(rows)
    p = os.path.join(out, 'output_checks.csv')
    K.atomic_write_csv(p, df)
    ok = not (df.status == 'FAIL').any()
    K.write_receipt('stage0_c6_output' + ('_rerun' if a.rerun else ''), [p, pp], 'SUCCEEDED' if ok else 'FAILED',
                    counts=df.status.value_counts().to_dict(), blocker=not ok)
    print(df.to_string(max_colwidth=120), flush=True)
    print(df.status.value_counts().to_dict(), 'OK' if ok else 'FAIL', flush=True)
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
