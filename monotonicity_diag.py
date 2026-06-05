"""
分组单调性诊断 + 跨段相关性核对 (单因子层面, 不做合成)
=====================================================
对 13 个因子 (现有4 + 候选9), 在 I11池+硬约束内, 用中性化后因子值固定 5 分组
(G1=最低..G5=最高, 不翻转, 看原始形状), 算每组相对池等权的超额(bp), 跨 4 段。
形状分类 → 归池建议 (合成池/规则池/距离化候选/人工复核)。
Part2: 复用全量已生成的 4 段相关性矩阵 CSV 做跨段核对 (不重跑回测)。

只复用四个地基模块 (data_loader/features_daily/event_study/pool_screening_v2),
不改它们, 也不依赖 comprehensive_factor_diagnosis.py。

用法:
  python monotonicity_diag.py [--factors all|a,b,c] [--periods all|p1,p2]
"""
import sys, os, argparse
import numpy as np, pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import data_loader
USER_CACHE_DIR = '/mnt/sda2/lichenchen/data/cache/'
os.makedirs(USER_CACHE_DIR, exist_ok=True)
data_loader.PATHS['cache_dir'] = USER_CACHE_DIR

from data_loader import load_all_daily_data
from features_daily import calc_all_daily_features
from event_study import PERIODS, get_base_pool
from pool_screening_v2 import (
    define_i11_signal, build_observation_pool, apply_hard_constraints,
    compute_reversal_skip1, compute_parkinson_vol, compute_abnormal_turnover,
    compute_cmf_change, compute_log_mcap, neutralize_by_mcap,
)

CORR_DIR_DEFAULT = '/mnt/sda2/lichenchen/results/20260605_0338_comprehensive_diag'
NEAR = ['2019-2023', '2024-2026']
FAR = ['2010-2014', '2015-2018']
ALL_PERIODS = ['2010-2014', '2015-2018', '2019-2023', '2024-2026']

CANDIDATES_9 = ['conditional_turnover', 'turnover_volatility_60d', 'stealth_score',
                'CCV_20d', 'CVR_20d', 'cum_intraday_ret_5d', 'cum_return_5d',
                'distance_from_high_20d', 'realized_kurtosis_20d']


def make_feat(name):
    def _f(data, features, industry):
        return features[name]
    return _f


def get_specs():
    specs = [
        {'name': 'reversal_skip1', 'func': lambda d, f, ind: compute_reversal_skip1(d['close'], ind, window=10)},
        {'name': 'parkinson_vol', 'func': lambda d, f, ind: compute_parkinson_vol(d['high'], d['low'], window=20)},
        {'name': 'abn_turnover', 'func': lambda d, f, ind: compute_abnormal_turnover(d.get('turnover_rate'), window_short=20, window_long=120)},
        {'name': 'cmf_change_neg', 'func': lambda d, f, ind: -compute_cmf_change(f, window_long=10, window_short=5)},
    ]
    specs += [{'name': n, 'func': make_feat(n)} for n in CANDIDATES_9]
    return specs


# ---------- forward return + 中性化 (与 comprehensive 同口径, 自包含) ----------
def compute_forward_5d_excess(data, base_pool, hold_days=5):
    vwap = data['vwap']
    bp = base_pool.reindex(index=vwap.index, columns=vwap.columns).fillna(0)
    vdr = (vwap / vwap.shift(1) - 1).replace([np.inf, -np.inf], np.nan)
    bm = vdr.where(bp == 1).mean(axis=1)
    exc = vdr.sub(bm, axis=0)
    fl = [exc.shift(-k) for k in range(2, 2 + hold_days)]
    return sum(fl) * 1e4


def precompute_neutralized(factor, filtered_pool, log_mcap):
    cache = {}
    for d in filtered_pool.index:
        if d not in factor.index:
            continue
        stocks = filtered_pool.columns[filtered_pool.loc[d] == 1].tolist()
        if len(stocks) < 6:
            continue
        fn = neutralize_by_mcap(factor.loc[d, stocks], log_mcap.loc[d, stocks])
        s = pd.DataFrame({'f': fn}).dropna()['f']
        if len(s) < 6:
            continue
        cache[d] = s
    return cache


def group_excess_sequence(neu_cache, forward_ret, n_groups=5):
    """固定 5 分组(不翻转), 返回 [G1..G5] 平均超额(bp) 和 使用天数."""
    dg = {g: [] for g in range(1, n_groups + 1)}
    nu = 0
    for d, fn in neu_cache.items():
        if len(fn) < n_groups * 3 or d not in forward_ret.index:
            continue
        df = pd.DataFrame({'f': fn, 'fw': forward_ret.loc[d, fn.index]}).dropna()
        if len(df) < n_groups * 3:
            continue
        try:
            df['g'] = pd.qcut(df['f'].rank(method='first'), n_groups, labels=range(1, n_groups + 1))
        except ValueError:
            continue
        for g in range(1, n_groups + 1):
            grp = df[df['g'] == g]
            if len(grp) > 0:
                dg[g].append(grp['fw'].mean())
        nu += 1
    if nu < 10:
        return None, nu
    return [float(pd.Series(dg[g]).mean()) for g in range(1, n_groups + 1)], nu


# ---------- 形状分类 (按 prompt 给的、已离线验证的算法) ----------
def classify_shape(seq):
    g = np.array(seq, dtype=float)
    n = len(g)
    info = {}
    gmax, gmin = float(np.nanmax(g)), float(np.nanmin(g))
    span = gmax - gmin
    info['span'] = span
    if not np.isfinite(span) or span <= 1e-9:
        return 'irregular', info
    imax, imin = int(np.argmax(g)), int(np.argmin(g))
    x = np.arange(n)
    coeffs = np.polyfit(x, g, 1)
    fit = np.polyval(coeffs, x)
    ss_res, ss_tot = float(np.sum((g - fit) ** 2)), float(np.sum((g - g.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    diffs = np.diff(g)
    pos, neg = int(np.sum(diffs > 0)), int(np.sum(diffs < 0))
    info.update(r2=r2, slope=float(coeffs[0]), pos_diffs=pos, neg_diffs=neg)
    # 1 倒U
    if imax in (1, 2, 3) and g[0] < gmax - 0.3 * span and g[-1] < gmax - 0.3 * span:
        return 'inverted_U', info
    # 2 U型
    if imin in (1, 2, 3) and g[0] > gmin + 0.3 * span and g[-1] > gmin + 0.3 * span:
        return 'U_shape', info
    # 3 单调 (R²>0.85 且相邻差至少 n-2 步同号)
    if r2 > 0.85 and (pos >= n - 2 or neg >= n - 2):
        return ('monotonic_up' if coeffs[0] > 0 else 'monotonic_down'), info
    # 4 单边 (中间3组幅度<0.35span, 且只一头明显偏负)
    mid = g[1:4]
    mid_amp = float(mid.max() - mid.min())
    m = float(mid.mean())
    d_low, d_high = g[0] - m, g[-1] - m
    info.update(mid_amp_frac=mid_amp / span, d_low=d_low, d_high=d_high)
    if mid_amp < 0.35 * span:
        if d_low < -0.3 * span and abs(d_low) > 1.5 * abs(d_high):
            return 'single_tail_low', info
        if d_high < -0.3 * span and abs(d_high) > 1.5 * abs(d_low):
            return 'single_tail_high', info
    # 5 弱单调 / 不规则
    if r2 > 0.5 and (pos >= n - 2 or neg >= n - 2):
        return ('weak_monotonic_up' if coeffs[0] > 0 else 'weak_monotonic_down'), info
    return 'irregular', info


def base_shape(s):
    if s is None:
        return ('none', None)
    if s.startswith('monotonic_'):
        return ('mono', s.split('_')[1])
    if s.startswith('single_tail_'):
        return ('single', s.split('_')[2])
    if s == 'inverted_U':
        return ('invU', None)
    if s == 'U_shape':
        return ('U', None)
    if s.startswith('weak_monotonic_'):
        return ('weakmono', s.split('_')[2])
    return ('irregular', None)


def pool_suggestion(shapes):
    """shapes: dict period->shape. 近段(2019/2024)权重高, 远段供参考."""
    near = [shapes.get(p) for p in NEAR]
    if any(s is None for s in near):
        return '人工复核(近段样本不足)', False
    b = [base_shape(s) for s in near]
    if b[0][0] == 'mono' and b[1][0] == 'mono' and b[0][1] == b[1][1]:
        return '合成池(单调%s)' % ('升' if b[0][1] == 'up' else '降'), True
    if b[0][0] == 'single' and b[1][0] == 'single' and b[0][1] == b[1][1]:
        return '规则池(%s)' % ('剔低' if b[0][1] == 'low' else '剔高'), True
    if b[0][0] == 'invU' and b[1][0] == 'invU':
        return '距离化候选(倒U)', True
    return '人工复核(近段形状不一致/U型)', False


# ---------- Part 2: 跨段相关性 (读已有 4 段矩阵) ----------
def load_corr(corr_dir):
    out = {}
    for p in ALL_PERIODS:
        fn = os.path.join(corr_dir, 'correlation_matrix_%s.csv' % p.replace('-', '_'))
        if os.path.exists(fn):
            out[p] = pd.read_csv(fn, index_col=0, encoding='utf-8-sig')
    return out


def corr4(cmats, a, b):
    vals = {}
    for p in ALL_PERIODS:
        m = cmats.get(p)
        if m is not None and a in m.index and b in m.columns:
            vals[p] = float(m.loc[a, b])
        else:
            vals[p] = np.nan
    return vals


def fmt4(vals):
    return ' '.join('%s=%+.2f' % (p[-4:], vals[p]) for p in ALL_PERIODS if not np.isnan(vals[p]))


# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--factors', default='all')
    ap.add_argument('--periods', default='all')
    ap.add_argument('--corr_dir', default=CORR_DIR_DEFAULT)
    args = ap.parse_args()

    specs = get_specs()
    if args.factors != 'all':
        want = [x.strip() for x in args.factors.split(',') if x.strip()]
        miss = [w for w in want if w not in {s['name'] for s in specs}]
        if miss:
            print('[STOP] 因子名对不上, 报告用户:', miss); return
        specs = [s for s in specs if s['name'] in want]
    periods = ALL_PERIODS if args.periods == 'all' else [p.strip() for p in args.periods.split(',')]

    out_dir = os.path.join('/mnt/sda2/lichenchen/results',
                           datetime.now().strftime('%Y%m%d_%H%M') + '_monotonicity_diag')
    os.makedirs(out_dir, exist_ok=True)
    print('输出目录:', out_dir)
    print('因子数: %d, 段: %s' % (len(specs), periods))

    # results[fac][period] = {'seq':[..], 'shape':str, 'n':int}
    results = {s['name']: {} for s in specs}

    for p in periods:
        start, end = PERIODS[p]
        print('\n=== 段 %s (%s~%s) 加载+计算 ===' % (p, start, end))
        data = load_all_daily_data(start_date=start, end_date=end)
        features = calc_all_daily_features(data)
        base_pool = get_base_pool(data)
        signal = define_i11_signal(features, base_pool)
        obs = build_observation_pool(signal, obs_window=5)
        filtered = apply_hard_constraints(obs, data, features, min_mcap=0)
        fwd = compute_forward_5d_excess(data, filtered, hold_days=5)
        log_mcap = compute_log_mcap(data.get('mcap'))
        industry = data.get('industry_zx1', data.get('industry'))
        if industry is not None:
            industry = industry.reindex(index=data['close'].index, columns=data['close'].columns)
        print('  池规模: %.0f 只/天' % filtered.sum(axis=1).mean())
        for s in specs:
            try:
                fac = s['func'](data, features, industry)
                cache = precompute_neutralized(fac, filtered, log_mcap)
                seq, nu = group_excess_sequence(cache, fwd, n_groups=5)
                if seq is None:
                    results[s['name']][p] = {'seq': None, 'shape': None, 'n': nu}
                    print('  %-24s n=%d (不足)' % (s['name'], nu))
                    continue
                shape, info = classify_shape(seq)
                results[s['name']][p] = {'seq': seq, 'shape': shape, 'n': nu, 'info': info}
                print('  %-24s n=%d  [%s] %s' % (s['name'], nu, shape,
                      '[' + ','.join('%.1f' % v for v in seq) + ']'))
            except Exception as e:
                results[s['name']][p] = {'seq': None, 'shape': None, 'n': 0, 'err': str(e)}
                print('  %-24s [ERROR] %s' % (s['name'], e))

    # ---- 存 CSV: 分组序列 + 形状 ----
    rows = []
    for fac, byp in results.items():
        for p in periods:
            r = byp.get(p, {})
            seq = r.get('seq')
            row = {'factor': fac, 'period': p, 'n_used': r.get('n'), 'shape': r.get('shape')}
            for i in range(5):
                row['G%d' % (i + 1)] = seq[i] if seq else np.nan
            rows.append(row)
    seq_df = pd.DataFrame(rows)
    seq_df.to_csv(os.path.join(out_dir, 'group_sequences.csv'), index=False, encoding='utf-8-sig')

    # ---- 图: 每因子 [G1..G5] 各段一条线 ----
    try:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        import warnings; warnings.filterwarnings('ignore')
        for fac, byp in results.items():
            fig, ax = plt.subplots(figsize=(7, 4.5))
            any_line = False
            for p in periods:
                seq = byp.get(p, {}).get('seq')
                if seq:
                    ax.plot(range(1, 6), seq, marker='o', label='%s [%s]' % (p, byp[p].get('shape')))
                    any_line = True
            if any_line:
                ax.axhline(0, color='k', lw=0.5); ax.set_xticks(range(1, 6))
                ax.set_xticklabels(['G1', 'G2', 'G3', 'G4', 'G5'])
                ax.set_title('%s | group excess (bp)' % fac); ax.legend(fontsize=7); ax.grid(alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(out_dir, 'shape_%s.png' % fac), dpi=100, bbox_inches='tight')
            plt.close()
    except Exception as e:
        print('[plot warn]', e)

    # ============ Part 2: 跨段相关性 ============
    cmats = load_corr(args.corr_dir)
    fac13 = [s['name'] for s in get_specs()]  # 始终全 13 (Part2 与 --factors 无关)
    ORIG = ['reversal_skip1', 'parkinson_vol', 'abn_turnover', 'cmf_change_neg']
    CAND = CANDIDATES_9
    # 反向组: 读全量 factor_metrics 的 2024 direction
    reverse_group = []
    fm_path = os.path.join(args.corr_dir, 'factor_metrics.csv')
    if os.path.exists(fm_path):
        fm = pd.read_csv(fm_path)
        d24 = fm[fm['period'] == '2024-2026'].set_index('factor')['direction'].to_dict()
        reverse_group = [f for f in fac13 if d24.get(f) == 'negative']

    # D1 现有4×候选: 2024低但他段高 (假象)
    d1 = []
    for o in ORIG:
        for c in CAND:
            v = corr4(cmats, o, c)
            others = [abs(v[p]) for p in FAR + ['2019-2023'] if not np.isnan(v[p])]
            if not np.isnan(v['2024-2026']) and abs(v['2024-2026']) < 0.5 and others and max(others) >= 0.6:
                d1.append((o, c, v))
    # D2 候选彼此 任意段|corr|>=0.5
    d2 = []
    for i in range(len(CAND)):
        for j in range(i + 1, len(CAND)):
            v = corr4(cmats, CAND[i], CAND[j])
            mx = max([abs(x) for x in v.values() if not np.isnan(x)] or [0])
            if mx >= 0.5:
                d2.append((CAND[i], CAND[j], v, mx))
    d2.sort(key=lambda t: -t[3])
    # D3 反向组两两
    d3 = []
    for i in range(len(reverse_group)):
        for j in range(i + 1, len(reverse_group)):
            v = corr4(cmats, reverse_group[i], reverse_group[j])
            d3.append((reverse_group[i], reverse_group[j], v))
    # D4 结论: 真冗余/漂移 (在 全13 任意对里)
    redun, drift = [], []
    allf = fac13
    for i in range(len(allf)):
        for j in range(i + 1, len(allf)):
            v = corr4(cmats, allf[i], allf[j])
            a = [abs(x) for x in v.values() if not np.isnan(x)]
            if len(a) < 2:
                continue
            if min(a) >= 0.6:
                redun.append((allf[i], allf[j], v, min(a)))
            elif max(a) - min(a) >= 0.3 and max(a) >= 0.6:
                drift.append((allf[i], allf[j], v, max(a) - min(a)))
    redun.sort(key=lambda t: -t[3]); drift.sort(key=lambda t: -t[3])

    # ============ 纯文本摘要 ============
    L = []
    L.append('=' * 78)
    L.append('分组单调性诊断 + 跨段相关性核对  (monotonicity_diag)  | 单因子层面, 不做合成')
    L.append('口径: I11池+硬约束, 中性化因子值, 固定5分组(G1低..G5高,不翻转), 每组相对池等权超额(bp), 5日fwd')
    L.append('段权重: 近段(2019-2023,2024-2026)>远段(2010-2014,2015-2018,仅参考不否决)')
    L.append('=' * 78)
    L.append('\n--- A. 每因子 4 段分组序列 [G1,G2,G3,G4,G5] (bp) ---')
    for s in specs:
        fac = s['name']; byp = results[fac]; segs = []
        for p in periods:
            seq = byp.get(p, {}).get('seq')
            segs.append('%s:[%s]' % (p[-4:], ','.join('%.1f' % v for v in seq) if seq else 'NA'))
        ns = ','.join('%s' % byp.get(p, {}).get('n') for p in periods)
        L.append('%-24s | %s | n(段)=%s' % (fac, ' '.join(segs), ns))
    L.append('\n--- B. 形状标签(各段) + 近段一致 + 归池建议 ---')
    for s in specs:
        fac = s['name']; byp = results[fac]
        shp = '/'.join('%s' % (byp.get(p, {}).get('shape') or 'NA') for p in periods)
        sugg, consistent = pool_suggestion({p: byp.get(p, {}).get('shape') for p in periods})
        L.append('%-24s | 形状(%s)=%s | 近段一致:%s | 建议:%s'
                 % (fac, '/'.join(p[-4:] for p in periods), shp, '是' if consistent else '否', sugg))
    L.append('\n--- C. 归池汇总 ---')
    buckets = {'合成池': [], '规则池': [], '距离化候选': [], '人工复核': []}
    for s in specs:
        sugg, _ = pool_suggestion({p: results[s['name']].get(p, {}).get('shape') for p in periods})
        key = ('合成池' if sugg.startswith('合成池') else '规则池' if sugg.startswith('规则池')
               else '距离化候选' if sugg.startswith('距离化') else '人工复核')
        buckets[key].append(s['name'] + (sugg[sugg.find('('):] if '(' in sugg else ''))
    for k in ['合成池', '规则池', '距离化候选', '人工复核']:
        L.append('%s: %s' % (k, ', '.join(buckets[k]) if buckets[k] else '(无)'))

    L.append('\n--- D. 跨段相关性核对 (复用全量4段矩阵, 未重跑回测) ---')
    L.append('阈值: 低<0.4, 中0.4-0.6, 高>=0.6; |corr| 跨段.')
    L.append('D1 现有4×候选 "2024-26低(<0.5)但他段>=0.6"(2024假象, 警惕):')
    if d1:
        for o, c, v in d1:
            L.append('   %s × %s: %s' % (o, c, fmt4(v)))
    else:
        L.append('   (无)')
    L.append('D2 候选彼此 任意段|corr|>=0.5 的对 (4段值, 降序):')
    if d2:
        for a, b, v, mx in d2:
            L.append('   %s × %s: %s' % (a, b, fmt4(v)))
    else:
        L.append('   (无)')
    L.append('D3 反向组(direction=反向: %s)两两4段相关:' % ', '.join(reverse_group))
    if d3:
        for a, b, v in d3:
            L.append('   %s × %s: %s' % (a, b, fmt4(v)))
    else:
        L.append('   (反向组不足或矩阵缺失)')
    L.append('D4 结论:')
    L.append('   真冗余(4段 min|corr|>=0.6, 建议合并/二选一):')
    if redun:
        for a, b, v, mn in redun:
            L.append('      %s × %s: %s  (min=%.2f)' % (a, b, fmt4(v), mn))
    else:
        L.append('      (无)')
    L.append('   段间漂移大(max-min|corr|>=0.3 且峰值>=0.6, 合成时小心):')
    if drift:
        for a, b, v, dd in drift:
            L.append('      %s × %s: %s  (漂移=%.2f)' % (a, b, fmt4(v), dd))
    else:
        L.append('      (无)')
    L.append('   其余对 4 段都低(<0.6), 视为相对独立 (略).')

    L.append('\n--- E. 异常 / 存疑 (需人工复核) ---')
    anomalies = []
    for s in specs:
        fac = s['name']; byp = results[fac]
        for p in periods:
            r = byp.get(p, {})
            if r.get('n') is not None and r.get('n') < 30 and r.get('seq') is None:
                anomalies.append('%s @%s: 样本不足 n=%s' % (fac, p[-4:], r.get('n')))
            info = r.get('info', {})
            if info and 0.7 < info.get('r2', 0) <= 0.85 and r.get('shape') not in ('monotonic_up', 'monotonic_down'):
                anomalies.append('%s @%s: R²=%.2f 接近单调阈值但未判为单调, 形状=%s (边界)' % (fac, p[-4:], info['r2'], r.get('shape')))
            if info and 0 < info.get('span', 1) < 2:
                anomalies.append('%s @%s: span=%.1fbp 极小, 形状判定不稳' % (fac, p[-4:], info['span']))
        # 近段不一致但远段强单调
        shps = {p: byp.get(p, {}).get('shape') for p in periods}
        nb = [base_shape(shps.get(p))[0] for p in NEAR]
        if 'mono' in nb and nb[0] != nb[1]:
            anomalies.append('%s: 近段形状不一致(%s) — 归人工复核' % (fac, '/'.join(str(shps.get(p)) for p in NEAR)))
    if anomalies:
        L.extend('- ' + a for a in anomalies)
    else:
        L.append('(自动检查未发现明显异常; 仍建议人工眼检 A 段序列核对标签)')

    summary = '\n'.join(L)
    with open(os.path.join(out_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write(summary)
    print('\n\n' + '#' * 78 + '\n# 纯文本摘要 (可复制) — 同时存 summary.txt\n' + '#' * 78)
    print(summary)
    print('\n[done] 输出:', out_dir)


if __name__ == '__main__':
    main()
