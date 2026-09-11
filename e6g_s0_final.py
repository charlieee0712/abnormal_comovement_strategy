#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-f: source_manifest.json + registry 汇总 + 复权敏感三分类 + 描述符/路径映射。"""
import os, sys, json, glob, hashlib, subprocess, time, platform
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6g_desc as GD
import e6e_core as K

CODE = '/mnt/sda2/lichenchen/code/project_core'
RES = G.RES
BRIEFS = '/mnt/sda2/lichenchen/exec_briefs_in'

FOUNDATION = ['data_loader.py', 'features_daily.py', 'event_study.py', 'pool_screening_v2.py']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def manifest():
    e6e = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6e_*.py')))
    e6f = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6f_*.py')))
    e6g = sorted(os.path.basename(p) for p in glob.glob(os.path.join(CODE, 'e6g_*.py')))
    out = dict(
        version=G.VERSION, written_at=time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        git_head=subprocess.check_output(['git', '-C', CODE, 'rev-parse', 'HEAD']).decode().strip(),
        git_head_short=subprocess.check_output(
            ['git', '-C', CODE, 'rev-parse', '--short', 'HEAD']).decode().strip(),
        frozen_end=G.FROZEN_END, results_dir=RES,
        foundation_readonly={f: sha(os.path.join(CODE, f)) for f in FOUNDATION},
        e6e_frozen={f: sha(os.path.join(CODE, f)) for f in e6e},
        e6f_frozen={f: sha(os.path.join(CODE, f)) for f in e6f},
        e6g_new={f: sha(os.path.join(CODE, f)) for f in e6g},
        counts=dict(foundation=len(FOUNDATION), e6e=len(e6e), e6f=len(e6f), e6g=len(e6g)),
        inputs={f: sha(os.path.join(BRIEFS, f)) for f in
                ['E6g_structure_layer.md', 'E6g_plan_web_final.md', 'E6g_proposal.md',
                 'E6f_REVIEW.md', 'E6f_REPORT_part1.md', 'E6f_REPORT_part2.md',
                 'E6f_REPORT_part3.md'] if os.path.exists(os.path.join(BRIEFS, f))},
        declared_in_brief=dict(
            plan='e5402a66d0a2c41e6c87dc72876faee835b481d5a75b913b67e8a78db0f606c2',
            e6f_review='1eda93b1e72fcbc85c69c8f42062bfdfed1c13aa9f598e9e5aad20885b4c3399',
            proposal='79f5632dbb743d19ba894bcffb137419a18dee8fc2a6bbb205916ca3d7ea912d'),
        runtime=dict(python=sys.version.split()[0], platform=platform.platform()),
        libs={},
        prior_dirs=dict(E6f=G.E6F_DIR, E6e=G.E6E_DIR, E6C=G.E6C_DIR),
    )
    for m in ('numpy', 'pandas', 'scipy', 'sklearn', 'pyarrow', 'statsmodels', 'numba'):
        try:
            out['libs'][m] = getattr(__import__(m), '__version__', '?')
        except Exception:
            out['libs'][m] = 'MISSING'
    # 输入指纹核对
    chk = []
    for nm, key in (('E6g_plan_web_final.md', 'plan'), ('E6f_REVIEW.md', 'e6f_review'),
                    ('E6g_proposal.md', 'proposal')):
        got = out['inputs'].get(nm)
        want = out['declared_in_brief'][key]
        chk.append(dict(file=nm, declared=want, actual=got, match=(got == want)))
    out['input_fingerprint_check'] = chk
    # 工作树: 只确认三个 2026-05 untracked 文件仍未被 add
    st = subprocess.check_output(['git', '-C', CODE, 'status', '--porcelain']).decode()
    out['git_status_porcelain'] = st.strip().split('\n')
    with open(os.path.join(RES, 'source_manifest.json'), 'w') as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print('source_manifest: 地基 %d / e6e %d / e6f %d / e6g %d; 指纹核对 %s'
          % (out['counts']['foundation'], out['counts']['e6e'], out['counts']['e6f'],
             out['counts']['e6g'], ['%s=%s' % (c['file'], c['match']) for c in chk]))
    return out


ADJ_KNOWN_UNKNOWN = [
    # 量/额/换手率类: 本轮的复权反事实只动价格, 没动股数/成交额, 所以"测出恒等"不构成证据
    'volume_ratio_1d', 'volume_ratio_3d', 'volume_ratio_5d', 'volume_zscore_60d',
    'volume_accel_3d', 'volume_trend_10d', 'volume_regime_break', 'volume_rank_market',
    'turnover_5d', 'turnover_rank_market', 'amount_ratio_1d', 'amount_concentration_5d',
    'amihud_daily', 'amihud_ratio_5d_20d', 'gap_volume_ratio', 'CMF_20d', 'mcap_rank',
    'conditional_turnover', 'turnover_volatility_60d', 'abn_turnover', 'stealth_score',
    'RPV_20d', 'drawdown_volume_ratio', 'amihud_asymmetry_20d', 'CCV_20d',
    'volume_momentum_divergence', 'inside_bar_freq_20d',
]


def registry_final():
    M = pd.read_csv(os.path.join(RES, 'registry', 'key_registry_meta.csv'))
    S = pd.concat([pd.read_csv(os.path.join(RES, 'registry', 'key_stats_%s.csv' % p))
                   for p in G.SEGMENTS], ignore_index=True)
    g = S.groupby('key').agg(
        adj_max_abs_diff=('adj_max_abs_diff', 'max'),
        adj_rank_change_frac=('adj_rank_change_frac', 'max'),
        maxabs=('maxabs', 'max'), mad=('mad', 'median'),
        q99_over_mad=('q99_over_mad', 'max'),
        nunique_raw=('nunique_raw', 'min'), tie_frac_raw=('tie_frac_raw', 'max'),
        max_tie_block_raw=('max_tie_block_raw', 'max'),
        missing_rate=('missing_rate', 'max'), inf_rate=('inf_rate', 'max'),
        ols_leverage_max_median=('ols_leverage_max_median', 'max'),
        n_valid_min=('n_valid', 'min')).reset_index()
    g['adj_rel'] = g.adj_max_abs_diff / g.maxabs.replace(0, np.nan)
    REL_TOL = 1e-11          # 低于此 = 浮点末位, 数学上恒等

    # 【两个独立标志, 不是互斥三分类】
    # (1) price_adj_measured_change: 只动价格的反事实里, 数值真的变了
    # (2) volume_dependent_untested: 表达式依赖股数/成交额/换手率, 本轮反事实【没动】这些,
    #     所以"测出恒等"不构成证据 —— 与 (1) 可以同时为真
    g['price_adj_measured_change'] = (g.adj_rel.notna() & (g.adj_rel >= REL_TOL))
    g['volume_dependent_untested'] = g.key.isin(ADJ_KNOWN_UNKNOWN)

    # (3) 单调变换键: 排名/分位是【某个底层键】的单调变换。若底层键实测不变,
    #     则该键的数值差只可能来自并列块被浮点噪声重排 -> 归入"并列驱动", 不算复权敏感。
    RANK_OF = {'gap_rank_in_sector': 'gap_zscore_20d',
               'overnight_ret_cross_sectional_rank': 'overnight_ret',
               'gap_percentile_60d': 'gap_abs_zscore_20d',
               'turnover_rank_market': 'turnover_5d',
               'volume_rank_market': 'volume_ratio_1d'}
    chg = dict(zip(g.key, g.price_adj_measured_change))
    g['rank_of'] = g.key.map(RANK_OF).fillna('')
    g['underlying_invariant'] = g.rank_of.map(lambda u: (not chg.get(u, True)) if u else None)
    g['tie_driven_rank_shift'] = (
        (~g.price_adj_measured_change | g.underlying_invariant.fillna(False))
        & (g.adj_rank_change_frac.fillna(0) > 0.01))
    # 单调变换且底层不变的, 从"真会变"里挪走
    g.loc[g.underlying_invariant.fillna(False), 'price_adj_measured_change'] = False

    def cls(r):
        if r['price_adj_measured_change'] and r['volume_dependent_untested']:
            return 'changes_and_volume_untested'
        if r['price_adj_measured_change']:
            return 'changes_under_price_adjustment'
        if r['volume_dependent_untested']:
            return 'unknown_share_count_not_tested'
        return 'invariant_under_price_adjustment'
    g['adj_class3'] = g.apply(cls, axis=1)
    R = M.merge(g, on='key', how='left')
    R.to_csv(os.path.join(RES, 'registry', 'key_registry.csv'), index=False)
    print('\n复权分类 (两个独立标志的交叉):')
    print(R.groupby('adj_class3').size().to_string())
    print('\n[A] 实测【价格复权下数值真的变】(%d):'
          % int(R.price_adj_measured_change.fillna(False).sum()))
    print(sorted(R.loc[R.price_adj_measured_change.fillna(False), 'key']))
    print('\n[B] 依赖股数/成交额, 本轮反事实未测 (%d):'
          % int(R.volume_dependent_untested.fillna(False).sum()))
    print(sorted(R.loc[R.volume_dependent_untested.fillna(False), 'key']))
    print('\n[C] 数值恒等 (或底层恒等) 但秩受并列翻转, WHOLE_TIE 必处理 (%d):'
          % int(R.tie_driven_rank_shift.fillna(False).sum()))
    print(sorted(R.loc[R.tie_driven_rank_shift.fillna(False), 'key']))
    print('\n[D] 单调变换键 (排名/分位) 与其底层键:')
    print(R.loc[R.rank_of.fillna('') != '',
                ['key', 'rank_of', 'underlying_invariant', 'adj_rank_change_frac']]
          .to_string(index=False))
    print('\n并列最重的 12 个键 (tie_frac / 最大 tie 块):')
    print(R.nlargest(12, 'tie_frac_raw')[['key', 'key_class', 'nunique_raw', 'tie_frac_raw',
                                          'max_tie_block_raw']].to_string(index=False))
    print('\n重尾最极端的 10 个键 (q99/MAD):')
    print(R.nlargest(10, 'q99_over_mad')[['key', 'q99_over_mad', 'maxabs',
                                          'missing_rate']].to_string(index=False))
    # J 集合与计数核对
    js = pd.DataFrame(dict(
        set_name=['U34', 'U35', 'NEW40', 'J_KTC', 'J_KT', 'CUSTOM4', 'CONFIRMED30'],
        n=[len(G.U34), len(G.U35), len(G.NEW40), len(G.J_KTC), len(G.J_KT),
           len(G.CUSTOM4), len(G.CONFIRMED30)],
        expected_in_brief=[34, 35, 40, 32, 33, 4, 30]))
    js['match'] = js.n == js.expected_in_brief
    js.to_csv(os.path.join(RES, 'registry', 'keyset_counts.csv'), index=False)
    print('\n键集合计数 vs brief:')
    print(js.to_string(index=False))
    pd.DataFrame(dict(key=G.J_KTC)).to_csv(os.path.join(RES, 'registry', 'J_KTC.csv'), index=False)
    pd.DataFrame(dict(key=G.J_KT)).to_csv(os.path.join(RES, 'registry', 'J_KT.csv'), index=False)
    return R


def display_path_map():
    """固定展示组的 descriptor -> path_key 映射 (去重表的种子)。"""
    rows = []
    for lab, cid, note in G.DISPLAY:
        cfg = GD.parse_cfg(cid)
        d = dict(core=cid.split('|')[0], veto=(cid.split('|')[1] if '|' in cid else None),
                 H=5, support='legacy_all', sel='SRC', tf='identity', dr='hi',
                 alpha=None, buf=None, tie='src', state=None, neu='NS', seed=None,
                 selector_veto='SRC')
        rows.append(dict(label=lab, descriptor_id=G.gid(cid), config_id=cid,
                         path_key=G.path_key(d), lineage=GD.core_lineage(cfg['core']).tag(),
                         veto_lineage=GD.veto_lineage(cfg['veto']).tag(), note=note))
    D_ = pd.DataFrame(rows)
    D_.to_csv(os.path.join(RES, 'registry', 'descriptor_path_map.csv'), index=False)
    print('\n展示组 descriptor -> path:')
    print(D_[['label', 'descriptor_id', 'path_key']].to_string(index=False))
    return D_


if __name__ == '__main__':
    manifest()
    registry_final()
    display_path_map()
