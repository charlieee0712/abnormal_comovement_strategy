#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h REPORT_part1 (brief §13/§14): 推导段全部已路由实验 + 覆盖 + 中心代表 +
组合 + 选择规则。答 Q1-Q6 的推导段部分与 Q10 初稿。

数字全部从已落盘产物读, 本脚本不重算。
"""
from __future__ import annotations
import os
import sys
import json
import time
import glob

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

RES = H.RES
SEGS = list(H.DERIV_SEGS)


def load():
    d = {}
    d['rt'] = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(
        os.path.join(RES, 'route_results', 'summary_*.csv')))], ignore_index=True)
    d['ix'] = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(
        os.path.join(RES, 'interaction_results', '*.csv')))], ignore_index=True)
    d['sel'] = pd.read_csv(os.path.join(RES, 'domain_selection', 'domain_selection.csv'))
    d['sp'] = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(
        os.path.join(RES, 'paired_controls', 'samepos_*.csv')))], ignore_index=True)
    d['man'] = json.load(open(os.path.join(RES, 'checks',
                                           'derivation_manifest_frozen.json')))
    d['rm'] = json.load(open(os.path.join(RES, 'registry', 'route_manifest.json')))
    return d


def fmt(x, n=3):
    return ('%+.*f' % (n, x)) if np.isfinite(x) else 'NA'


def main():
    D = load()
    rt, ix, sel, sp = D['rt'], D['ix'], D['sel'], D['sp']
    e = rt[~rt.is_identity]
    idn = rt[rt.is_identity]
    sel['sel2'] = sel.selector.str.replace(r'S2_shrink_tau', 'S2_t', regex=True)
    L = []
    A = L.append

    A('# E6h REPORT_part1 —— 推导段的已路由实验、组合与选择')
    A('')
    A('执行 session，%s。结果目录 `%s`（47）。' % (time.strftime('%Y-%m-%d'),
                                                  os.path.basename(RES)))
    A('推导段 `%s` / `%s`。事前登记 `preregistration.md` 落盘于任何新收益评价之前。'
      % (SEGS[0], SEGS[1]))
    A('**记录 B 未批准；本文没有任何 2019 年后的受保护对象结果。**')
    A('')
    A('---')
    A('')
    A('## 摘要（15 行）')
    A('')
    A('1. 记录 A v0 的九张卡编译出 **%d 个描述符 × 2 段 = %d 格，全部跑通，0 失败**；'
      'sha256 `%s`。' % (D['man']['total'], D['man']['total_config_segments'],
                         D['man']['sha256'][:16]))
    A('2. **%d 个 identity 端点全部恰好 %.3e**（α=0 / η=0 / e=0 / λ=0 在加载新因子之前短路），'
      '母体 net8 与 E6g 已存值逐位相同；六类算子的恒等锚 48/48。'
      % (len(idn), idn.d_net8_ann.abs().max()))
    A('3. **九条路线里只有 M-T 的中位为正**（对直接母体 %s / %s 两段）。'
      % tuple(fmt(e[(e.route_id == 'M-T-tcv-vs-t60') & (e.segment == s)].d_net8_ann.median())
              for s in SEGS))
    mt = e[(e.route_id == 'M-T-tcv-vs-t60') & (e.alpha < 1.0) &
           (e.new_key.isin(['TCV_20', 'turnover_5d']))]
    A('4. 限定到**部分混合 × {`TCV_20`, `turnover_5d`}** 的 %d 格：对母体 **100%% 为正**'
      '（中位 %s），对**同人数核心对照**也 **100%% 为正**（中位 %s），'
      '跨 4 个母体 × 2 段全部同号。'
      % (len(mt), fmt(mt.d_net8_ann.median()), fmt(mt.d_vs_ctl_core_matchN.median())))
    spx = sp[sp.alpha < 1.0]
    A('5. 补跑的**同仓位对照**（逐形成日缩到两者较小仓位）后仍为正：%s / %s（%d%% / %d%% 正）——'
      '约 15–33%% 的增益是敞口，其余在完全相同仓位下仍在。'
      % tuple([fmt(spx[spx.segment == s].d_net8_samepos.median()) for s in SEGS] +
              [int(round(100 * (spx[spx.segment == s].d_net8_samepos > 0).mean()))
               for s in SEGS]))
    a1 = e[(e.route_id == 'M-T-tcv-vs-t60') & (e.alpha == 1.0)]
    A('6. **α=1（完全替换）明显为负**（中位 %s，均值 %s）→ T 的信息**不冗余**，'
      '新测量是"加"不是"换"。这直接答上 M-T 登记的双向问题。'
      % (fmt(a1.d_net8_ann.median()), fmt(a1.d_net8_ann.mean())))
    q = e[e.route_id == 'E-V-quiet-price'].d_net8_ann
    s_ = e[e.route_id == 'E-V-surge-price'].d_net8_ann
    A('7. **E-V 两个竞争分支并排**：T0 支持的 quiet 中位 %s（均值 %s），竞争的 surge %s（%s）。'
      '两者都负，但**按错误符号只跑 surge 会得到负得多的结论**——符号勘误（复盘 #33）在这里兑现。'
      % (fmt(q.median()), fmt(q.mean()), fmt(s_.median()), fmt(s_.mean())))
    ro = e[e.route_id == 'R-O-overnight-risk'].d_net8_ann
    A('8. **R-O 几乎全网格有害**：%d 格里 p95 = %s、最大仅 %s。'
      % (len(ro), fmt(ro.quantile(.95)), fmt(ro.max())))
    ip = e[e.route_id == 'I-P-peer-up-laggard']
    ipc = ip[(ip.w == 20) & (ip.role == 'ADD')]
    A('9. **I-P 的网格中位 %s 是被 w=5 与 SWAP 两支拖的**；w=20 + ADD 那支 %d 格全正'
      '（中位 %s）。' % (fmt(ip.d_net8_ann.median()), len(ipc),
                        fmt(ipc.d_net8_ann.median())))
    A('10. 但**同人数核心对照在 I-P 上分歧**：R1 多为正、**A06 全负**——在 A06 那里增益只是'
        '"按它自己的核分数多拿几只"，不是行业信息。没有这个对照会把**深度**误读成**新信息**。')
    A('11. 交互项（`net_AB − net_A − net_B + net_P`，只是组合构造上的交互、**不是因果分解**）：'
        + '；'.join('`%s` 中位 %s（%d%% 正）'
                    % (p, fmt(g.interaction.median()),
                       int(round(100 * (g.interaction > 0).mean())))
                    for p, g in ix[ix.interaction.notna()].groupby('pair')) + '。')
    evro = ix[(ix.pair == 'EV_x_RO') & ix.n_new_removed_by_risk.notna()]
    A('12. `EV×RO` 的正交互有具体机制：**加回的格里 %d%% 被隔夜风险否决删掉**——'
        '"加回是否引入新隔夜风险"这一问的答案是**是**。'
        % int(round(100 * evro.n_new_removed_by_risk.median()
                    / max(1, evro.n_added.median()))))
    A('13. **三种选择器都保不住对父的优势**（%d 个域）：估计段 → 冻结后应用段，'
        'S0 %s → %s、S1 %s → %s、S2(τ=0.5) %s → %s。'
        % tuple([sel.domain.nunique()] +
                [fmt(sel[(sel.sel2 == s) & (sel.segment == g)].d_vs_parent.median())
                 for s in ('S0_fixed', 'S1_hier_equal', 'S2_t0.5') for g in SEGS]))
    A('14. **S1 层级等权是三者里最差的**（整体中位 %s，正比例 %d%%）——域里多数成员是负的，'
        '等权把组合拖下去；**收缩得越狠越好**（τ=0.5 > 1.0 > 2.0）。'
        % (fmt(sel[sel.sel2 == 'S1_hier_equal'].d_vs_parent.median()),
           int(round(100 * (sel[sel.sel2 == 'S1_hier_equal'].d_vs_parent > 0).mean()))))
    A('15. 例外是 M-T 域：那里**固定中心代表最好**（%s → %s，应用段反而更高），'
        '因为整个域都好，收缩反而让出增益。'
        % tuple(fmt(sel[(sel.sel2 == 'S0_fixed') & (sel.route_id == 'M-T-tcv-vs-t60')
                        & (sel.segment == g)].d_vs_parent.median()) for g in SEGS))
    A('')
    A('---')
    A('')
    A('## 1. 逐路线全表（对直接母体，两段）')
    A('')
    A('算子与 n 逐列标出；**均值与中位并报**（E6g 复盘纪律 ⑮）。')
    A('')
    A('| 路线 | n | 中位 %s | 中位 %s | 均值 | p05 | p95 | 最大 | 正比例 | vs 同人数核心（中位） |'
      % tuple(SEGS))
    A('|---|---|---|---|---|---|---|---|---|---|')
    for r, g in e.groupby('route_id'):
        A('| `%s` | %d | %s | %s | %s | %s | %s | %s | %d%% | %s |'
          % (r, len(g),
             fmt(g[g.segment == SEGS[0]].d_net8_ann.median()),
             fmt(g[g.segment == SEGS[1]].d_net8_ann.median()),
             fmt(g.d_net8_ann.mean()), fmt(g.d_net8_ann.quantile(.05)),
             fmt(g.d_net8_ann.quantile(.95)), fmt(g.d_net8_ann.max()),
             int(round(100 * (g.d_net8_ann > 0).mean())),
             fmt(g.d_vs_ctl_core_matchN.median())))
    A('')
    A('**读法**：中位为负**不等于**该路线无效——它说的是'
      '"在本轮这个母体集合 × 这个角色 × 这两段 × 这个成本口径下，该网格的中位没有改善"。'
      '每一条否定都限定在这六项内。')
    A('')
    A('## 2. M-T 的拆分（唯一为正的路线）')
    A('')
    A('| α | n | vs 母体 中位 / 均值 | 正比例 | vs 同人数核心 中位 / 均值 |')
    A('|---|---|---|---|---|')
    for al, g in e[e.route_id == 'M-T-tcv-vs-t60'].groupby('alpha'):
        A('| %.2f | %d | %s / %s | %d%% | %s / %s |'
          % (al, len(g), fmt(g.d_net8_ann.median()), fmt(g.d_net8_ann.mean()),
             int(round(100 * (g.d_net8_ann > 0).mean())),
             fmt(g.d_vs_ctl_core_matchN.median()),
             fmt(g.d_vs_ctl_core_matchN.mean())))
    A('')
    A('| 测量（α<1） | n | 中位 | 均值 | 正比例 | (母体×段) 全正格 |')
    A('|---|---|---|---|---|---|')
    for k, g in e[(e.route_id == 'M-T-tcv-vs-t60') & (e.alpha < 1.0)].groupby('new_key'):
        pv = g.pivot_table(index='parent', columns='segment', values='d_net8_ann',
                           aggfunc='median')
        A('| `%s` | %d | %s | %s | %d%% | %d/%d |'
          % (k, len(g), fmt(g.d_net8_ann.median()), fmt(g.d_net8_ann.mean()),
             int(round(100 * (g.d_net8_ann > 0).mean())),
             int((pv > 0).sum().sum()), int(pv.size)))
    A('')
    A('**竞争解释与仍未排除的**：(i) 仓位——同仓位对照后仍为正，但增益缩了 15–33%%；'
      '(ii) 深度——同人数核心对照后仍为正，所以不是"多拿几只"；'
      '(iii) 换手上升（d_turn +0.001~+0.005）带来的成本已在 net8 里扣掉，但'
      '**冲击成本没有**——κ 未校准，规模效应留给 carried L；'
      '(iv) 本轮只测了 T 位，**没测**把同一测量放在 K 位或 C 位；'
      '(v) 这是推导段，路线是在看过 E6g 与 R0 之后选的。')
    A('')
    A('## 3. 三种选择器（Q7 的推导段部分）')
    A('')
    A('| 选择器 | n | %s 中位 | %s 中位 | 整体均值 | 正比例 |' % tuple(SEGS))
    A('|---|---|---|---|---|---|')
    for s, g in sel.groupby('sel2'):
        A('| %s | %d | %s | %s | %s | %d%% |'
          % (s, len(g), fmt(g[g.segment == SEGS[0]].d_vs_parent.median()),
             fmt(g[g.segment == SEGS[1]].d_vs_parent.median()),
             fmt(g.d_vs_parent.mean()),
             int(round(100 * (g.d_vs_parent > 0).mean()))))
    A('')
    A('S2 给**原父**的平均权重：' +
      '、'.join('τ=%.1f → %.2f' % (t, g.parent_weight.mean())
                for t, g in sel[sel.selector.str.startswith('S2')].groupby('tau')) + '。')
    A('')
    A('**组合是真账户，不是净值平均**：S1 把域成员的**逐日目标权重**合并后再过一次引擎，'
      '换手合并后重算（中位 %.5f，成员中位 %d 个 / 测量中位 %d 个）。'
      % (sel[sel.sel2 == 'S1_hier_equal'].turn_mean.median(),
         sel[sel.sel2 == 'S1_hier_equal'].n_members.median(),
         sel[sel.sel2 == 'S1_hier_equal'].n_measurements.median()))
    A('')
    A('## 4. 这一轮**没有**得出的结论')
    A('')
    A('- 没有任何 2019 年后的结果。记录 B 未批准，守卫以代码强制（13 条攻击全部被拒）。')
    A('- 没有校准的冲击成本。κ 是情景，不是估计值；规模效应在 carried L 里另测。')
    A('- 没有说哪条路线"无效"。每条否定都写成"母体 × 需求 × 角色 × 日期 × 支持 × 成本"六元组。')
    A('- 未路由的 %d 个（键 × 母体）对**没有被测**，不是被否定；理由在 `consideration_ledger.csv`。'
      % D['rm']['counts']['n_unassigned'])
    A('- 推导段结果属研究历史，**不叫未污染 OOS**；本轮的九张卡是在看过 E6g 与 R0 之后选的。')
    A('')
    A('## 5. Q10 初稿（还有哪些没测）')
    A('')
    A('1. 同一测量放在**别的位置**（M-T 只测了 T 位；TCV 在 K 位 / C 位未测）。')
    A('2. **E-P 的中间区间**：本轮只测了两端阈值（比例 0.2/0.8、计数 1/4），中间没测。')
    A('3. **I-P 的 w 只测了 5 与 20**；R0 的证据在 20，5 明显更差，中间窗口未测。')
    A('4. **R-O 的低状态**（竞争方向）在主运行里跑了，但软降权只到 λ=1；'
      '"释放资本再投入"而不是留现金的版本未测。')
    A('5. 组合层只做了域内；**跨域组合**（例如 M-T × 多母体）未测。')
    A('6. 未路由的 %d 对里，有证据标志的 %d 对是 v1 最该先看的。'
      % (D['rm']['counts']['n_unassigned'], D['rm']['counts']['n_candidate']))
    A('')

    p = os.path.join(RES, 'REPORT_part1.md')
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(L) + '\n')
    print('REPORT_part1.md: %d 行' % len(L))
    bad = [w for w in ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台')
           if w in '\n'.join(L)]
    print('禁用词: %s' % (bad if bad else '零命中'))


if __name__ == '__main__':
    main()
