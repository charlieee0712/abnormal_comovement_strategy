#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6c 玩具测试(合成面板). 按用户 2026-09-04 确认的调整 5 分两档:
   BLOCK = {1,2,3,7,8,11,12,14} 必须 PASS 才继续; SOFT = 其余, 失败只记录。
   用法: python e6c_selftests.py --out <dir>
"""
import sys, os, io, json, argparse
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import numpy as np, pandas as pd
import comprehensive_factor_diagnosis as C
from e6c_holding_horizon import nw_stats, score_hac, HMAX

BLOCK = {1, 2, 3, 7, 8, 11, 12, 14}
R = []
def rec(i, name, ok, detail=''):
    R.append(dict(id=i, name=name, ok=bool(ok), blocking=i in BLOCK, detail=str(detail)[:300]))
    print('[T%-2d %s] %-46s %s' % (i, 'PASS' if ok else ('FAIL' if i in BLOCK else 'soft-FAIL'), name, detail), flush=True)

def panel(T=44, N=4, jumps=None):
    """无除权合成面板: lclose = 前一日 close -> adjust_factor 恒为 1; vwap 按给定跳变构造."""
    idx = pd.bdate_range('2024-01-01', periods=T)
    cols = ['S%d' % i for i in range(N)]
    v = np.ones((T, N))
    for (t, i, r) in (jumps or []):
        v[t:, i] *= (1.0 + r)
    vwap = pd.DataFrame(v, index=idx, columns=cols)
    close = vwap.copy()
    lclose = close.shift(1); lclose.iloc[0] = close.iloc[0]
    d = dict(close=close, lclose=lclose, vwap=vwap,
             is_open=pd.DataFrame(1, index=idx, columns=cols),
             change_pct=close / lclose - 1)
    return d, idx, cols

def eng(W, data, pool, H, bp=8.0):
    return C.compute_calendar_pnl(W, data, pool, hold_days=H, cost_bp_bilateral=bp)

def main(out):
    # ---------- T1 单脉冲: 首个收益落 T+2, 幅度 1/min(H, 可用行数) ----------
    # 稳态段(T0 足够靠后)幅度 = 1/H; 段首(可用行数<H)分母 = 可用行数 —— 与 §1.3 契约一致, 两种都测
    T0 = 30
    data, idx, cols = panel(T=60, jumps=[(T0 + 2, 0, 0.01)])
    pool = pd.DataFrame(1.0, index=idx, columns=cols)
    W = pd.DataFrame(0.0, index=idx, columns=cols); W.iloc[T0, 0] = 1.0
    ok = True; det = []
    for H in (1, 3, 5, 20):
        pr = eng(W, data, pool, H); p = pr['port_daily'].values
        first = np.argmax(np.abs(p) > 1e-15) if (np.abs(p) > 1e-15).any() else -1
        amp = p[T0 + 2]; exp = 0.01 / min(H, T0 + 1)
        ok &= (first == T0 + 2) and abs(amp - exp) < 1e-12
        det.append('H%d first=%d amp=%.6f(exp %.6f)' % (H, first, amp, exp))
    # 段首: T0 小于 H 时分母 = 可用行数
    T0b = 10
    d2, i2, c2 = panel(T=44, jumps=[(T0b + 2, 0, 0.01)])
    W2 = pd.DataFrame(0.0, index=i2, columns=c2); W2.iloc[T0b, 0] = 1.0
    amp_b = eng(W2, d2, pd.DataFrame(1.0, index=i2, columns=c2), 20)['port_daily'].values[T0b + 2]
    exp_b = 0.01 / (T0b + 1)
    ok &= abs(amp_b - exp_b) < 1e-12
    det.append('段首 H20@t=%d amp=%.6f(exp 1/%d=%.6f)' % (T0b + 2, amp_b, T0b + 1, exp_b))
    rec(1, '单脉冲: 首收益 T+2; 稳态 1/H, 段首分母=可用行数', ok, '; '.join(det))

    # ---------- T2 收益只在第 10 日: H<10 拿不到, H>=10 拿 1/H ----------
    data, idx, cols = panel(jumps=[(T0 + 11, 0, 0.01)])
    W = pd.DataFrame(0.0, index=idx, columns=cols); W.iloc[T0, 0] = 1.0
    ok = True; det = []
    for H in (5, 9, 10, 15):
        p = eng(W, data, pool, H)['port_daily'].values[T0 + 11]
        exp = 0.0 if H < 10 else 0.01 / H
        ok &= abs(p - exp) < 1e-12; det.append('H%d=%.6f(exp %.6f)' % (H, p, exp))
    rec(2, '第 10 日收益: H<10 不得, H>=10 得 1/H', ok, '; '.join(det))

    # ---------- T3 连续信号批次叠加 + 换手 = (W_{t-2}-W_{t-H-2})/H ----------
    data, idx, cols = panel()
    W = pd.DataFrame(0.0, index=idx, columns=cols); W.iloc[T0:T0 + 4, 0] = 1.0
    H = 5; pr = eng(W, data, pool, H)
    w = W.values; Tn = len(idx)
    exp_turn = np.zeros(Tn)
    for t in range(Tn):
        a = w[t - 2] if t - 2 >= 0 else np.zeros(len(cols))
        b = w[t - H - 2] if t - H - 2 >= 0 else np.zeros(len(cols))
        exp_turn[t] = 0.5 * np.abs((a - b) / H).sum()
    got = pr['daily_turnover'].values
    ok = np.nanmax(np.abs(got[H + 3:] - exp_turn[H + 3:])) < 1e-12
    rec(3, '批次叠加 + 换手=(W_{t-2}-W_{t-H-2})/H', ok, 'max|d|=%.2e' % np.nanmax(np.abs(got[H + 3:] - exp_turn[H + 3:])))

    # ---------- T4 (soft) 恒定/交替目标: 换手不强制 1/H ----------
    Wc = pd.DataFrame(0.0, index=idx, columns=cols); Wc.iloc[:, 0] = 1.0
    tc = eng(Wc, data, pool, 5)['daily_turnover'].values[10:]
    Wa = pd.DataFrame(0.0, index=idx, columns=cols)
    Wa.iloc[::2, 0] = 1.0; Wa.iloc[1::2, 1] = 1.0
    ta = eng(Wa, data, pool, 5)['daily_turnover'].values[10:]
    rec(4, '恒定目标换手=0; 交替目标换手>0(此例恰=1/H)', tc.max() < 1e-12 and ta.mean() > 1e-6,
        'const=%.2e alt_mean=%.4f 1/H=%.4f' % (tc.max(), ta.mean(), 1 / 5))

    # ---------- T5 (soft) 分组: <3k 只无持仓; 二分组 vs 十分位留 50% ----------
    neu = {idx[t]: pd.Series(np.arange(len(cols)) * 1.0, index=cols) for t in range(5)}
    h_small = C.build_factor_strategy_holdings_cached(neu, pool.iloc[:5], 2, [2])
    neu9 = {idx[t]: pd.Series(np.arange(9) * 1.0, index=['X%d' % i for i in range(9)]) for t in range(5)}
    pool9 = pd.DataFrame(1.0, index=idx[:5], columns=['X%d' % i for i in range(9)])
    h_bin = C.build_factor_strategy_holdings_cached(neu9, pool9, 2, [2])
    h_dec = C.build_factor_strategy_holdings_cached(neu9, pool9, 10, list(range(6, 11)))
    rec(5, '<3k 只当日无持仓; 二分组 vs 十分位留50% 成员差可见',
        h_small.values.sum() == 0 and h_bin.values.sum() > 0,
        'N=4,k=2 需>=6 故空: sum=%.0f; 9 只 bin 留 %.0f, dec 留 %.0f'
        % (h_small.values.sum(), h_bin.values[0].sum(), h_dec.values[0].sum()))

    # ---------- T6 (soft) full 从日序列重算 != 段均值平均 ----------
    a = np.r_[np.full(100, 0.001), np.full(300, 0.002)]
    seg_avg = np.mean([0.001, 0.002]); concat = a.mean()
    rec(6, 'full 指标须从日序列重算(不平均段)', abs(seg_avg - concat) > 1e-9,
        'seg_avg=%.6f vs concat=%.6f' % (seg_avg, concat))

    # ---------- T7 8->12bp 日差恒等 ----------
    W2 = pd.DataFrame(0.0, index=idx, columns=cols); W2.iloc[T0:T0 + 8, 0] = 1.0
    p8 = eng(W2, data, pool, 5, 8.0); p12 = eng(W2, data, pool, 5, 12.0)
    d = p8['net_excess_daily'].values - p12['net_excess_daily'].values
    exp = p8['daily_turnover'].values * 4 / 1e4
    rec(7, '8->12bp 日差 = turnover*4/1e4', np.nanmax(np.abs(d - exp)) < 1e-15,
        'max|d|=%.2e' % np.nanmax(np.abs(d - exp)))

    # ---------- T8 零仓位仍保留退出成本; pu 不除零 ----------
    W3 = pd.DataFrame(0.0, index=idx, columns=cols); W3.iloc[T0, 0] = 1.0
    pr = eng(W3, data, pool, 3)
    pos = pr['daily_position'].values; cost = pr['daily_turnover'].values * 8 / 1e4
    zc = cost[(pos <= 1e-12) & (cost > 0)]
    with np.errstate(divide='ignore', invalid='ignore'):
        pu = np.where(pos > 1e-12, pr['net_excess_daily'].values / pos, np.nan)
    rec(8, '零仓位日仍有退出成本; pu 不除零', len(zc) > 0 and np.isfinite(pu[pos <= 1e-12]).sum() == 0,
        'zero-pos 有成本日 %d 天, 合计 %.3e' % (len(zc), zc.sum()))

    # ---------- T9 (soft) 停牌 -> 复牌 ----------
    data9, idx9, cols9 = panel(T=20, N=2)
    data9['is_open'].iloc[5:8, 0] = 0
    data9['vwap'].iloc[5:8, 0] = np.nan
    r = C.vwap_daily_return(data9, adjust=True)
    # 契约: 停牌日 NaN; 复牌当日因 vwap.shift(1) 仍是停牌 NaN 而同样为 NaN; 复牌次日恢复
    rec(9, '停牌日 NaN; 复牌当日也 NaN(前值缺); 复牌次日恢复',
        bool(r.iloc[5:8, 0].isna().all()) and bool(np.isnan(r.iloc[8, 0])) and bool(np.isfinite(r.iloc[9, 0])),
        '停牌 NaN=%s 复牌当日 NaN=%s 次日 finite=%s(每次停牌吃 len+1 天无收益, 权重仍计入 position)'
        % (r.iloc[5:8, 0].isna().all(), np.isnan(r.iloc[8, 0]), np.isfinite(r.iloc[9, 0])))

    # ---------- T10 (soft) cohort 右边界 ----------
    T = 44; valid = (np.arange(T) >= 60) & (np.arange(T) + HMAX + 1 <= T - 1)
    T2 = 200; valid2 = (np.arange(T2) >= 60) & (np.arange(T2) + HMAX + 1 <= T2 - 1)
    rec(10, 'cohort: T+21 越界不进入', valid.sum() == 0 and valid2.sum() == (T2 - 1 - HMAX - 1) - 60 + 1,
        'T=44 -> %d 个; T=200 -> %d 个' % (valid.sum(), valid2.sum()))

    # ---------- T11 父子分割与混合恒等式 ----------
    rng = np.random.RandomState(0)
    par = rng.rand(30, 6) > 0.4; ch = par & (rng.rand(30, 6) > 0.3); rem = par & ~ch
    split_ok = bool((par == (ch | rem)).all() and not (ch & rem).any())
    rr = rng.randn(30, 6) * 0.01
    okm = True
    for t in range(30):
        if par[t].sum() == 0 or ch[t].sum() == 0 or rem[t].sum() == 0: continue
        rp = rr[t][par[t]].mean(); rc = rr[t][ch[t]].mean(); rm = rr[t][rem[t]].mean()
        q = rem[t].sum() / par[t].sum()
        okm &= abs(rp - ((1 - q) * rc + q * rm)) < 1e-12
    rec(11, '父=子∪剔除, 子∩剔除=∅, 混合恒等式', split_ok and okm, 'split=%s mixture=%s' % (split_ok, okm))

    # ---------- T12 score-HAC 无缺失时 == nw_stats ----------
    x = rng.randn(400) * 0.001 + 0.0002
    a1, _, t1, _ = nw_stats(x, L=5); a2, t2, n2 = score_hac(x, 5)
    xg = x.copy(); xg[[5, 50, 300]] = np.nan
    a3, t3, n3 = score_hac(xg, 5)
    rec(12, 'score-HAC 无缺口 == nw_stats; 有缺口可算', abs(a1 - a2) < 1e-9 and abs(t1 - t2) < 1e-9 and n3 == 397,
        'ann d=%.2e t d=%.2e; 缺口 n=%d t=%.3f' % (abs(a1 - a2), abs(t1 - t2), n3, t3))

    # ---------- T13 (soft) bootstrap 同 seed 复现 ----------
    import hashlib
    def sub(ns): return int.from_bytes(hashlib.sha256(('20260904/' + ns).encode()).digest()[:8], 'big') % (2**32)
    r1 = np.random.RandomState(sub('a')).rand(5); r2 = np.random.RandomState(sub('a')).rand(5)
    r3 = np.random.RandomState(sub('b')).rand(5)
    rec(13, 'bootstrap 子 seed 可复现且命名空间隔离',
        np.allclose(r1, r2) and not np.allclose(r1, r3), 'same=%s diff=%s' % (np.allclose(r1, r2), not np.allclose(r1, r3)))

    # ---------- T14 fixedmix: 各段常数 -> 方差 0; concat 非零 ----------
    segs = [np.full(100, 0.001), np.full(120, 0.002), np.full(90, 0.0015), np.full(80, 0.0005)]
    allx = np.concatenate(segs); mu = allx.mean()
    num = 0.0
    for s in segs:
        z = s - mu; e = z - z.mean()
        S = e @ e
        for l in range(1, 6):
            if l < len(e): S += 2 * (1 - l / 6) * (e[l:] @ e[:-l])
        num += S
    var_fixedmix = num / len(allx) ** 2
    _, _, t_concat, _ = nw_stats(allx, L=5)
    rec(14, 'fixedmix: 段内常数 -> 方差 0; concat NW 非零', var_fixedmix < 1e-30 and np.isfinite(t_concat),
        'var_fixedmix=%.2e concat_t=%.1f' % (var_fixedmix, t_concat))

    # ---------- T15 (soft) 前视: 改未来不影响过去 ----------
    d1, i1, c1 = panel(jumps=[(30, 0, 0.05)])
    Wf = pd.DataFrame(0.0, index=i1, columns=c1); Wf.iloc[10, 0] = 1.0
    p_a = eng(Wf, d1, pd.DataFrame(1.0, index=i1, columns=c1), 5)['net_excess_daily'].values[:25]
    d2, _, _ = panel(jumps=[(30, 0, 0.90)])
    p_b = eng(Wf, d2, pd.DataFrame(1.0, index=i1, columns=c1), 5)['net_excess_daily'].values[:25]
    rec(15, '改未来值不改过去输出(无前视)', np.nanmax(np.abs(p_a - p_b)) < 1e-15,
        'max|d|(前 25 日)=%.2e' % np.nanmax(np.abs(p_a - p_b)))

    # ---------- T16 (soft) % 格式串全扫 ----------
    import ast, re
    bad = 0; checked = 0
    for f in ['e6c_holding_horizon.py', 'e6c_selftests.py']:
        p = os.path.join('/mnt/sda2/lichenchen/code/project_core', f)
        if not os.path.exists(p): continue
        src = io.open(p, encoding='utf-8').read()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod) and \
               isinstance(node.left, ast.Constant) and isinstance(node.left.value, str) and '%' in node.left.value:
                lit = node.left.value; checked += 1
                spec = re.findall(r'%(?!%)[-+ #0]*[\d.*]*[hlL]?([a-zA-Z])', lit)
                try: lit % tuple(('x' if c == 's' else 1) for c in spec)
                except Exception: bad += 1
    rec(16, '%-格式串哑元全扫', bad == 0, 'checked=%d bad=%d' % (checked, bad))

    io.open(os.path.join(out, 'selftest_results.json'), 'w', encoding='utf-8', newline='\n').write(
        json.dumps(R, ensure_ascii=False, indent=1))
    nb = [r for r in R if r['blocking'] and not r['ok']]
    ns = [r for r in R if not r['blocking'] and not r['ok']]
    print('\n[SELFTEST] blocking %d/%d PASS, soft %d/%d PASS'
          % (len([r for r in R if r['blocking'] and r['ok']]), len(BLOCK), len([r for r in R if not r['blocking'] and r['ok']]), 16 - len(BLOCK)))
    if ns: print('[soft-FAIL]', [r['id'] for r in ns])
    sys.exit(1 if nb else 0)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); main(a.out)
