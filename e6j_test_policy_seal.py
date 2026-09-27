# -*- coding: utf-8 -*-
"""E6j 自测（不读真实结果）：bootstrap 计数矩阵与 bootstrap_full 同 draw、政策三态判定（e-随机 MC 状态、e-资本 0 容差、市值 N/A、失败优先于未定）、
封存版本追加 / 核对、MC 增补计划。全部在临时目录的合成文件上运行，结束后删除该临时目录（不在 results/ 下）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import shutil
import tempfile

import numpy as np
import pandas as pd

TMP = tempfile.mkdtemp(prefix='e6j_selftest_', dir='/mnt/sda2/lichenchen')
os.environ['E6J_RES'] = TMP      # 在导入 e6j_core 之前：全部读写（含回执）都落在临时目录
import e6j_core as J             # noqa: E402
assert J.RES == TMP
import e6j_seal as SEAL          # noqa: E402
import e6j_policy_p as PP        # noqa: E402
import e6j_mc_topup as MT        # noqa: E402
SEAL.RES = TMP
MT.RAN = os.path.join(TMP, 'randoms', 'P')
res = []


def check(name, ok, detail=''):
    res.append(dict(test=name, status='PASS' if ok else 'FAIL', detail=str(detail)[:200]))


def t_bands():
    """计数矩阵形式与 ST.bootstrap_full 同 draw 逐值一致；逐年位置口径与直接重放一致；中心化版本同。"""
    import e6j_stats as ST
    import e6j_bands as BD
    rng = np.random.default_rng(5)
    spans = {J.SEGMENTS[0]: ('2010-01-04', 300), J.SEGMENTS[1]: ('2011-03-01', 250), J.SEGMENTS[2]: ('2012-02-01', 280), J.SEGMENTS[3]: ('2013-06-03', 120)}
    dates = {s: pd.bdate_range(a, periods=n).strftime('%Y-%m-%d').values for s, (a, n) in spans.items()}
    d = {s: np.where(rng.random(n) < 0.05, np.nan, rng.normal(2e-4, 3e-3, n)) for s, (a, n) in spans.items()}
    lens = {s: len(dates[s]) for s in J.SEGMENTS}
    cm = BD.count_mats(lens, dates, 20, 200, 'T-bands')
    for centered in (False, True):
        ref = ST.bootstrap_full(d, 20, 200, 'T-bands', centered)
        rs = BD.resample(cm, {s: d[s][:, None] for s in J.SEGMENTS}, centered=centered)
        got = BD.full(rs, J.SEGMENTS)[:, 0]
        check('计数矩阵 FULL = bootstrap_full（centered=%s）' % centered, np.nanmax(np.abs(got - ref)) < 1e-10, np.nanmax(np.abs(got - ref)))
    # 逐年（位置日历）直接重放
    r2 = J.rng_for('E6j', 'bootstrap', 'T-bands', 20)
    idx = {s: [ST.stationary_indices(lens[s], 20, r2) for _ in range(200)] for s in J.SEGMENTS}
    rs = BD.resample(cm, {s: d[s][:, None] for s in J.SEGMENTS})
    yp, ys = BD.years_pos(rs)
    direct = []
    for b in range(200):
        cnt = 0
        for y in ys:
            vals = []
            for s in J.SEGMENTS:
                yr = pd.to_datetime(pd.Index(dates[s])).year.values
                x = d[s][idx[s][b]][yr == y]
                vals += list(x[np.isfinite(x)])
            if vals and np.mean(vals) > 0:
                cnt += 1
        direct.append(cnt)
    check('逐年正数（位置日历）= 直接重放', np.array_equal(yp[:, 0], np.array(direct)), (yp[:5, 0], direct[:5]))
    b0 = ST.bootstrap_full(d, 20, 200, 'T-bands')           # 实值取重采样中心（测试只核 max-t 的量纲，不核偏差）
    q, sd, plo, phi, slo, shi, fam = BD.max_t_band(np.column_stack([b0, b0 + 1.0]), np.array([b0.mean(), b0.mean() + 1.0]))
    check('max-t 同时带：完全相关两列 q 接近逐点 1.96 且 ≥ 1.9', np.isfinite(q) and 1.9 <= q <= 2.2 and fam.all(), q)


def t_policy():
    post = list(J.POST_SEGS)
    cases = [([0.5, 0.3], [.01, .01], 'PASS'), ([0.5, -0.3], [.01, .01], 'FAIL'), ([0.5, 0.01], [.01, .01], 'MC_UNRESOLVED'),
             ([0.5, -0.01], [.01, .01], 'MC_UNRESOLVED'), ([0.5, 0.0], [.01, 0.0], 'FAIL'), ([np.nan, 0.5], [.01, .01], 'NA'),
             ([-0.5, np.nan], [.01, .01], 'FAIL'), ([0.05, 0.05], [.04, .01], 'MC_UNRESOLVED'), ([0.2, 0.2], [.05, .05], 'PASS')]
    df = pd.DataFrame([{**{'rand_IID_%s' % s: d[i] for i, s in enumerate(post)}, **{'mcse_IID_%s' % s: e[i] for i, s in enumerate(post)}}
                       for d, e, _ in cases])
    got = PP.e_rand_status(df, post)
    check('e_rand_status 九例', got == [c[2] for c in cases], got)
    ts = PP.tri_sign([1e-12, -1e-12, 0.2, -0.2, np.nan])
    check('tri_sign 0 容差', list(ts[:4]) == [0.0, 0.0, 1.0, -1.0] and np.isnan(ts[4]), ts)
    base = dict(arm='S', c_FULL_d10=True, d_ok=True, f_FULL_d10=True, positive_FULL=True, e_cap_FULL='PASS', e_rand='PASS', size_status='PASS')
    V = lambda **kw: PP.verdict(pd.Series({**base, **kw}), 'FULL')
    exp = [(V(), '通过'), (V(e_rand='MC_UNRESOLVED'), '不可判（e随机:MC_UNRESOLVED）'),
           (V(e_rand='MC_UNRESOLVED', c_FULL_d10=False), '不通过（c）'), (V(size_status='FAIL'), '不通过（市值通道）'),
           (V(size_status='N/A（无两边都有的编辑日）'), '通过'), (V(e_cap_FULL='NA'), '不可判（e资本:NA）'),
           (V(arm='COL:K_rarpre'), '列对象（不评分）'), (V(positive_FULL=False, e_rand='FAIL'), '不通过（正向门槛、e随机）')]
    check('verdict 八例', all(a == b for a, b in exp), [a for a, b in exp if a != b])


def touch(rel, payload=b'x'):
    p = os.path.join(TMP, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as f:
        f.write(payload)
    return p


def receipt(name, status='SUCCEEDED'):
    touch('task_status/%s.receipt.json' % name, json.dumps(dict(status=status)).encode())


def fake_shard(seg, form, arm, path0, n, sd, seed):
    rng = np.random.default_rng(seed)
    ann = np.zeros((1, n, 3, 4, 4)); ann[0, :, :, :, 0] = rng.normal(0.0, sd, (n, 3, 4))
    p = os.path.join(TMP, 'randoms', 'P', seg, '%s__%s%s.npz' % (form, arm, '' if path0 == 0 else '_p%d' % path0))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    np.savez(p, mechs=np.array(['IID']), alphas=np.array([0.125, 0.25, 0.5]), Hs=np.array([3, 5, 10, 20]), path0=np.array([path0]), ann=ann)
    receipt('run_prand_%s_%s_%s%s' % (seg, form, arm, '' if path0 == 0 else '_p%d' % path0))


def t_seal_and_topup():
    os.makedirs(os.path.join(TMP, 'registration')); os.makedirs(os.path.join(TMP, 'checks'))
    for s in J.SEGMENTS:
        for i, f in enumerate(MT.FORMS):
            touch('accounts/P/%s/%s.npz' % (s, f), f.encode()); receipt('run_p_%s_%s' % (s, f))
            for j, a in enumerate(MT.ARMS_MAIN):
                big = (s == J.POST_SEGS[0] and f == 'A4b_CVRv5' and a == 'S')
                fake_shard(s, f, a, 0, 1024, 1.2 if big else 0.5, 1000 * i + j)
    rc = SEAL.main('P')
    check('封存 v1 回执齐全', rc == 0 and os.path.exists(SEAL.seal_path('P', 1)))
    check('verify v1', SEAL.verify('P')[0])
    MT.main()
    q = open(os.path.join(TMP, 'logs', 'queue_mc_topup_P_round1.txt')).read().splitlines()
    c = pd.read_csv(os.path.join(TMP, 'checks', 'mc_topup_P_round1.csv'))
    check('增补计划：只大 sd 的一组、2 个 512 分片、path0 1024 / 1536', len(q) == 2 and all('--arm S ' in x and 'A4b_CVRv5' in x for x in q)
          and '--path0 1024 ' in q[0] and '--path0 1536 ' in q[1], q)
    check('增补计划：格数 = 2 段 × 6 形态 × 4 臂 × 12', len(c) == 2 * 6 * 4 * 12, len(c))
    seg = J.POST_SEGS[0]
    fake_shard(seg, 'A4b_CVRv5', 'S', 1024, 512, 1.2, 7); fake_shard(seg, 'A4b_CVRv5', 'S', 1536, 512, 1.2, 8)
    ok, bad = SEAL.verify('P')
    check('增补后未封存 → verify 不过', (not ok) and any(b.startswith('<未封存>') for b in bad), bad[:2])
    rc = SEAL.main('P'); s2 = json.load(open(SEAL.seal_path('P', 2)))
    check('封存 v2：增补 2 回执 / 2 文件、新增 2', rc == 0 and s2['receipts_topup'] == 2 and s2['topup_files'] == 2 and len(s2['new_files']) == 2, s2['new_files'])
    check('verify v2', SEAL.verify('P')[0])
    x, _, _, end, spans = MT.iid_paths(seg, 'A4b_CVRv5', 'S')
    check('合并路径 2,048、下一个 path_index 2048', x.shape[0] == 2048 and end == 2048, (x.shape, end, spans))
    MT.main()
    q2 = open(os.path.join(TMP, 'logs', 'queue_mc_topup_P_round2.txt')).read().splitlines()
    check('第二轮：MCSE ≤ .03 后不再增补', len(q2) == 0, q2)
    # 精确臂名：S 的分片不混入 SM
    PP.RAN = MT.RAN; PP._RCACHE.clear()
    ref = PP.random_ref(seg, 'A4b_CVRv5', 'S', 0.25, 5, 0.0)
    ref_sm = PP.random_ref(seg, 'A4b_CVRv5', 'SM', 0.25, 5, 0.0)
    check('random_ref 合并 S 全部分片、SM 不混入', ref['npaths_IID_%s' % seg] == 2048 and ref_sm['npaths_IID_%s' % seg] == 1024,
          (ref['npaths_IID_%s' % seg], ref_sm['npaths_IID_%s' % seg]))
    # 缺回执的增补文件 → 回执不齐
    np.savez(os.path.join(TMP, 'randoms', 'P', seg, 'A4b__M_p1024.npz'), x=np.zeros(1))
    rc = SEAL.main('P')
    check('增补文件缺回执 → 封存 all_succeeded = False', rc == 2 and not SEAL.verify('P')[0])
    # 已封存文件被改 → 不得追加
    touch('accounts/P/%s/A4b.npz' % J.SEGMENTS[0], b'changed')
    try:
        SEAL.main('P'); raised = False
    except RuntimeError:
        raised = True
    check('已封存文件被改 → 拒绝追加版本', raised)
    check('verify 发现被改文件', not SEAL.verify('P')[0])


if __name__ == '__main__':
    try:
        t_bands()
        t_policy()
        t_seal_and_topup()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    df = pd.DataFrame(res)
    print(df.to_string())
    sys.exit(0 if (df.status == 'PASS').all() else 1)
