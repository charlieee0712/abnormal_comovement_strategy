#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i 记录 B 草稿 (brief §7 / §14): 按【需求域包】组织 (不是 <= 12 单格)。每包列全部成员、强度、期限、对照、方向 / 状态、
读法优先级 (策略问题 vs 机制问题)、Z-MEAN / Z-MAP 零期望、源 SHA; 用户可批准整个清单或明确子集; 允许"空建议";
考虑过未进后段的项留理由。执行端的建议 = 全部包 (完整登记, 不按推导段结果挑, 避免赢家诅咒) —— 用户定。
输出 reports/E6i_record_B_draft.md 与 registry/record_B_candidate_manifest.json (待批准的冻结清单 + SHA)。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import json
import glob
import time
import hashlib

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
CODE = '/mnt/sda2/lichenchen/code/project_core'
MAIN = ('RT', 'RK', 'RV', 'RR', 'RO', 'RC', 'RA', 'RS', 'RL', 'TPAIR', 'FOURARM')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def a0_version():
    import re
    vs = [int(m.group(1)) for m in (re.search(r'A0_amendment_v1_(\d+)\.md$', x) for x in
                                    glob.glob(os.path.join(R, 'registry', 'A0_amendment_v1_*.md'))) if m]
    return 'v1.%d' % max(vs) if vs else 'v1.0'


def main():
    a0 = pd.read_csv(os.path.join(R, 'registry', 'descriptors_A0.csv'), low_memory=False)
    stf = pd.read_csv(os.path.join(R, 'statistics', 'descriptor_stats_full.csv'), low_memory=False) \
        if os.path.exists(os.path.join(R, 'statistics', 'descriptor_stats_full.csv')) else None
    pk = []
    for (rt, mo), g in a0[a0.route_id.isin(MAIN + ('M1', 'M2'))].groupby(['route_id', 'mother_id']):
        rec = dict(package='E6I-B-%s-%s' % (rt, mo), route=rt, mother=mo, n_descriptors=len(g),
                   n_members=g.member_id.nunique(), roles='|'.join(sorted(g.role.astype(str).unique())),
                   strengths='|'.join(sorted(g.strength.astype(str).unique()))[:80],
                   H='|'.join(str(h) for h in sorted(g.H.astype(int).unique())),
                   directions='|'.join(sorted(g.direction.astype(str).unique())))
        if stf is not None:
            s = stf[stf.descriptor_id.isin(g.descriptor_id)]
            if len(s):
                rec['deriv_full_median'] = float(s.d_net8_ann.median())
                rec['deriv_full_share_pos'] = float((s.d_net8_ann > 0).mean())
                rec['deriv_n_ci_excl0_pos'] = int((s.ci_excludes_zero & (s.d_net8_ann > 0)).sum())
                rec['deriv_n_ci_excl0_neg'] = int((s.ci_excludes_zero & (s.d_net8_ann < 0)).sum())
                rec['null_expected_ci_excl0'] = round(0.05 * len(s), 1)
                rec['se_median'] = float(s.se_nwH.median())
                rec['mde80_median'] = float((2.8 * s.se_nwH).median())
        pk.append(rec)
    P = pd.DataFrame(pk)
    files = sorted(glob.glob(os.path.join(CODE, 'e6i_*.py'))) + sorted(glob.glob(os.path.join(CODE, 'e6i_vendor', '**', '*.py'),
                                                                               recursive=True))
    man = dict(round='E6i', stage='record_B_candidate', written_at=time.strftime('%Y-%m-%d %H:%M:%S'),
               descriptors_sha256=sha(os.path.join(R, 'registry', 'descriptors_A0.csv')),
               m2_spec_sha256=sha(os.path.join(R, 'registry', 'M2_program_spec.md')),
               preregistration_sha256=sha(os.path.join(R, 'preregistration.md')),
               code_sha256={os.path.relpath(f, CODE): sha(f) for f in files},
               packages=P.package.tolist(), n_descriptors=int(P.n_descriptors.sum()),
               post_segments=list(I.POST_SEGS), end_date='2026-03-27',
               rules=['两后段 (2019-23 / 2024-01..2026-03-27) 同一 manifest 全部计算并封存, receipt 后共同展示',
                      '不看 2019-23 后改 2024-26', 'M2 年度更新按本清单冻结规则用当时已成熟历史执行并留日志',
                      '后段技术修复保持经济定义并记 hash', '批准只解封清单内对象; 其他新成员不因此解封'])
    I.atomic_write_json(os.path.join(R, 'registry', 'record_B_candidate_manifest.json'), man)
    I.atomic_write_csv(os.path.join(R, 'registry', 'record_B_candidate_packages.csv'), P)
    msha = sha(os.path.join(R, 'registry', 'record_B_candidate_manifest.json'))
    L = []
    w = L.append
    w('# E6i 记录 B 草稿（需求域包；待用户批准）\n')
    w('生成于 %s（47 时间）。**这是草稿，不是批准**：后段（2019-01..2026-03-27）在用户批准前一律不跑任何新测量 / 新算子 / '
      'M1 / M2 对象；C1 / C2 的旧输入格可先算封存、B 前不读。\n' % time.strftime('%Y-%m-%d %H:%M'))
    w('## 1. 批准什么\n')
    w('- 批准对象 = 下表的**需求域包**（路线 x 母体）。可以批整张表、明确子集（按包名），或"没有一项值得推进"。')
    w('- 批准后执行端核 SHA（`registry/record_B_candidate_manifest.json`，sha `%s…`）后打开守卫（E6I-B- 命名空间，'
      '只解封清单内对象），两后段按同一 manifest **一次算完并封存**，receipt 后共同展示；**不看 2019-23 后改 2024-26**。' % msha[:12])
    w('- 后段读法（事前登记，不因结果改）：策略问题 = 对真实母体的同成本、同 H 配对 net8（主）；机制问题 = 同人数核心 / '
      '同资本 / 反向；逐年、LOYO（单列 2020 / 2024+）、去 2015+16 不适用于后段；三层同步带、δ 尺度与 MDE、四个状态词。')
    w('- M2 程序按 `registry/M2_program_spec.md` 冻结（basis / λ 网格 / 年度更新 / 回退 / 预算），后段年度更新用当时已成熟历史执行并留日志。')
    w('- **后段不是 OOS**：它是冻结对象的首次观察；功效有限（见 MDE 列）。\n')
    w('## 2. 执行端的建议（用户定）\n')
    w('**建议批准全部包（完整登记）。** 理由：(1) E6f 已示范"在族内按推导段结果挑"选不出比族中位更好的政策账户（赢家诅咒 > 族优势），'
      '后段首次观察的价值在于冻结对象的整体分布，而不是挑出来的格；(2) 后段计算便宜（主账户与推导段同量级，随机对照不必复跑）；'
      '(3) 部分批准会让后段读数带上"按推导段结果选择"的偏差，削弱它作为首次观察的意义。')
    w('若用户倾向更小的清单，**按包整体取舍**（不在包内挑强度 / H），并把未批包写进"考虑过未进后段"。\n')
    w('## 3. 需求域包\n')
    w('> **汇总算子**：包内描述符计数与推导段点估分布 ｜ **分母及构成**：包内全部 A0 %s 描述符 ｜ **基准**：同 H 母体 ｜ '
      '**子集**：主路线 + M1 + M2 ｜ **单位**：年化百分点 ｜ **日期支持**：推导两段合并（full） ｜ **H**：见列 ｜ '
      '**成本**：8bp ｜ **支持口径**：各段有效日 ｜ **资本口径**：源 DEV\n' % a0_version())
    cols = [c for c in ('package', 'n_descriptors', 'n_members', 'roles', 'H', 'deriv_full_median', 'deriv_full_share_pos',
                        'deriv_n_ci_excl0_pos', 'deriv_n_ci_excl0_neg', 'null_expected_ci_excl0', 'se_median',
                        'mde80_median') if c in P.columns]
    Q = P[cols].copy()
    out = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for _, r in Q.iterrows():
        out.append('| ' + ' | '.join(('%.3f' % v) if isinstance(v, float) else str(v) for v in r.values) + ' |')
    w('\n'.join(out) + '\n')
    w('**零期望**（Z-MEAN / 读表参照）：若包内全部增量为零，NW 95% 区间"排除 0"的描述符约占 5%（列 null_expected_ci_excl0，'
      '实际相关性使其方差更大）；Z-MEAN 的家族中位 / 最大 / 两段同号零分布见 `statistics/zmean_family.csv`；'
      'Z-MAP（局部无信息映射）只在推导段跑，后段不复跑。MDE80 = 在当前精度下 80% 功效能分辨的年化差（后段更短，MDE 更大）。\n')
    w('## 4. 冻结清单与源 SHA\n')
    w('- 描述符：`registry/descriptors_A0.csv`（A0 %s，%d 个，sha `%s…`）；M2 规格 sha `%s…`；preregistration sha `%s…`。'
      % (a0_version(), len(a0), man['descriptors_sha256'][:12], man['m2_spec_sha256'][:12],
         man['preregistration_sha256'][:12]))
    w('- 代码：%d 个 e6i 源文件的 SHA 列在 manifest（`code_sha256`）。\n' % len(man['code_sha256']))
    w('## 5. 考虑过未进后段的项\n')
    w('- 本草稿不预设排除任何 A0 包；用户若只批子集，未批包在此登记理由。考虑过但本轮未构造的测量见 `reports/consideration_ledger_E6i.md` C 部分。\n')
    txt = '\n'.join(L)
    for b in ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台'):
        assert b not in txt, b
    open(os.path.join(R, 'reports', 'E6i_record_B_draft.md'), 'w', encoding='utf-8').write(txt)
    print('B 草稿: 包 %d / 描述符 %d; manifest sha %s' % (len(P), int(P.n_descriptors.sum()), msha[:12]))


if __name__ == '__main__':
    main()
