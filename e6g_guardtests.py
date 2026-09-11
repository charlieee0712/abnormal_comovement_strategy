#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 阶段 0-c: 40 键血缘守卫的四条攻击测试 (brief 硬约束 2 / §12)。
   四条【必须被拒】, 且 cvr_1d 原式的历史使用【不得被误封】。证据落 checks/。
"""
import os, sys, json, traceback
sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6g_core as G
import e6e_core as K

OUT = os.path.join(G.RES, 'checks')
R = []


def expect_reject(name, fn, note=''):
    try:
        fn()
        R.append(dict(test=name, expect='REJECT', got='PASSED', ok=False, note=note, detail=''))
    except G.GuardViolation as e:
        R.append(dict(test=name, expect='REJECT', got='REJECTED', ok=True, note=note,
                      detail=str(e)[:300]))
    except Exception as e:
        R.append(dict(test=name, expect='REJECT', got='OTHER_ERROR:%s' % type(e).__name__,
                      ok=False, note=note, detail=traceback.format_exc()[-400:]))


def expect_pass(name, fn, note=''):
    try:
        fn()
        R.append(dict(test=name, expect='PASS', got='PASSED', ok=True, note=note, detail=''))
    except Exception as e:
        R.append(dict(test=name, expect='PASS', got='%s' % type(e).__name__, ok=False,
                      note=note, detail=str(e)[:300]))


# ---- a. 重命名新键 (两条路: 显示别名 / 公式别名) ----
G.register_alias('momo_alpha', 'volume_accel_3d')          # 给 NEW40 键换个无辜名字
expect_reject('a1_rename_alias_holding_2019',
              lambda: G.guard(G.lin_of_spec(G.specF('momo_alpha')), 'holding',
                              segment='2019-2023', where='attack_a1'),
              '别名 momo_alpha -> volume_accel_3d, 2019 段建持仓')
expect_reject('a2_formula_alias_CVR_trade_2024',
              lambda: G.guard(G.lin_of_spec(G.specF('CVR')), 'trade',
                              segment='2024-2026', where='attack_a2'),
              'CVR 与 intraday_cvr_1d 同公式, 但 CVR 是 NEW40 登记名, 不继承祖父豁免')
expect_reject('a3_unregistered_key_spec',
              lambda: G.assert_registered_spec(G.specF('my_secret_factor'), 'attack_a3'),
              '自造键名不在 U35 / NEW40 -> 规格层就挡住')
expect_reject('a4_unknown_role_spec',
              lambda: G.assert_registered_spec(dict(role='Z', w=1), 'attack_a4'),
              '自写公式换个新角色 -> 角色层挡住')

# ---- b. 由新键拟合的学习产物 ----
tree_lin = G.learned_lineage(G.Lin.of(K.FK), G.Lin.of(K.FT), G.Lin.of('volume_zscore_60d'))
expect_reject('b1_learned_tree_selection_2019',
              lambda: G.guard(tree_lin, 'selection', segment='2019-2023', where='attack_b1'),
              '坐标含 NEW40 的树 -> 输出标签继承血缘, 2019 段选择被拒')
expect_reject('b2_learned_cluster_outcome_2024',
              lambda: G.guard(tree_lin, 'outcome_cluster', segment='2024-2026',
                              where='attack_b2'),
              'kmeans 同理')

# ---- c. 2018 跨年标签 ----
expect_reject('c1_label_end_crosses_2018',
              lambda: G.guard(G.Lin.of('amihud_daily'), 'label', segment='2015-2018',
                              label_end='2019-01-07', where='attack_c1'),
              '2018-12-27 形成日的 5 日标签端点落到 2019 -> 被拒')
expect_pass('c2_label_end_inside_2018',
            lambda: G.guard(G.Lin.of('amihud_daily'), 'label', segment='2015-2018',
                            label_end='2018-12-24', where='attack_c2'),
            '端点仍在 2018 内 -> 放行')

# ---- d. 2019 只建持仓、不读收益 ----
expect_reject('d1_holding_only_2019',
              lambda: G.guard(G.Lin.of('turnover_5d'), 'holding', segment='2019-2023',
                              label_end=None, where='attack_d1'),
              '只建持仓不读收益也被拒 (use_type=holding 在禁列)')
expect_reject('d2_cost_only_2024',
              lambda: G.guard(G.Lin.of('turnover_5d'), 'cost', segment='2024-2026',
                              where='attack_d2'),
              '只算成本也被拒')

# ---- e. cvr_1d 原式不被误封 ----
for seg_ in G.SEGMENTS:
    expect_pass('e_cvr1d_grandfathered_%s' % seg_,
                lambda s=seg_: G.guard(G.lin_of_spec(G.specF(K.FCVR1)), 'trade',
                                       segment=s, where='grandfather'),
                'intraday_cvr_1d 是 E6e 已登记的 U35 键, 全段合法')
expect_pass('e_KTC_all_segments',
            lambda: G.guard(G.Lin.of(K.FK, K.FT, K.FC, K.FCR5), 'trade',
                            segment='2024-2026', where='grandfather'),
            'K/T/C/cr5 全是 U34/U35, 全段合法')
# 推导段内 NEW40 的合法用法必须放行 (守卫不能把 K 块也封了)
expect_pass('e_new40_ok_in_derivation',
            lambda: G.guard(G.Lin.of('amihud_daily'), 'trade', segment='2010-2014',
                            label_end='2014-12-31', where='K2'),
            'NEW40 在推导段 + label_end <= 2018 -> 放行')

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'guard_attack_tests.json'), 'w') as fh:
    json.dump(dict(results=R, guard_log=G.guard_log()), fh, indent=1, ensure_ascii=False)

nbad = sum(1 for r in R if not r['ok'])
for r in R:
    print('%-38s expect=%-6s got=%-14s %s' % (r['test'], r['expect'], r['got'],
                                              'OK' if r['ok'] else '*** FAIL ***'))
print('\n40 键守卫攻击测试: %d/%d 通过' % (len(R) - nbad, len(R)))
sys.exit(1 if nbad else 0)
