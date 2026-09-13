#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""记录 B 批准并跑完后段之后, 把 coverage.csv 的闸门条目改成实际状态。

只改四条 blocked_by_gate + 新增两行 (part3 / first_look_receipts) + 一条 changed 收口。
原因逐条写进 reason_or_impact, 不覆盖既有理由。
"""
from __future__ import annotations
import os
import sys
import glob

import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H

R = H.RES


def n_files(pat):
    return len(glob.glob(os.path.join(R, pat)))


UPDATES = {
    '记录 B: 用户 + 规划 session 冻结后段清单': dict(
        status='done', evidence='registration/record_B_approved.json',
        n_evidence_files=1,
        reason_or_impact=('用户看过 record_B_draft.md 后一次性批准整份草稿 (未改任何一条), '
                          '2026-09-13 11:39:52 冻结; 清单 SHA c6a95478e4b18097, 66 个描述符 '
                          '(52 M-T + 14 I-P-peer-up); 未批准 7 条路线, 逐条理由在案。'
                          '守卫自检 5/5: 未批准 route_id 与空 route_id 均被拒。'
                          '批准出处如实记录为"整份草稿的一次性批准, 不是逐条签署"')),
    '后段首次观察 (2019-2023 / 2024-2026)': dict(
        status='done',
        evidence='post_segments/SEALED_post_2019-2023.csv',
        n_evidence_files=10,
        reason_or_impact=('两后段按同一冻结清单一次算完并封存 (292 行 x 2), receipt 的清单 SHA '
                          '与批准时逐位相同, 输出 SHA 开封前后一致; 补 post_extra (逐年/单年留一/'
                          'NW t/vs R1@H5/vs R2@H5)、post_family_bands (F-route 与 F-headline, '
                          'block 20/60, 共同抽样 2000 draws)、post_selection (S0/S1/S2)、'
                          'random_refs_post (U_IID/I_IID/I_P20)。'
                          '**这不是 OOS**, 边界写在 REPORT_part2 开头')),
    'REPORT_part2': dict(
        status='done', evidence='REPORT_part2.md', n_evidence_files=1,
        reason_or_impact=('按 plan §10.3 五类归属写完; 无任何一条落进"有改善点估且值得继续"。'
                          'B-02 按事前登记的"先看匹配随机"读法, 与相对母体的读数在 2019-2023 '
                          '不一致, 已按规则以匹配随机为准并写明')),
    '新主路线在记录 B 指定的中心代表与 S1 组合上补 b{0,10} x H{3,5,15,20}': dict(
        status='done', evidence='L/L_newroute_grid_2019-2023.csv', n_evidence_files=8,
        reason_or_impact=('记录 B 批准后补跑 256 格 (2 中心代表 + 6 个 S1 组合) x b{0,10} x '
                          'H{3,5,15,20} x 四段。可持有域按子名单定义 '
                          '(Bmask(b) = 子名单 | 母体核放宽 b 档新开的一圈), 否则 b=0 复现不了'
                          '子名单 (直接用母体放宽域实测差 4,536 格)。b=0 阻断锚 62/62 x 4 段。'
                          '结果: b=10 对 I-P-peer-up 的修复在后段最大且换手几乎不变 (全在 gross)')),
    '三次交付 + 两次记录的运行组织': dict(
        status='done', evidence='REPORT_part3.md', n_evidence_files=3,
        reason_or_impact=('part1 (推导段) / part2 (后段首次观察) / part3 (carried L-T 全覆盖 + '
                          '四段合并地图 + 全轮 coverage) 三次交付全部完成; '
                          '记录 A v0 由执行端生效, 记录 A v1 属规划 session; 记录 B 已批准')),
}

NEW_ROWS = [
    dict(brief_section='§14', item='REPORT_part3 (carried L/T 全覆盖 + 四段合并地图 + 全轮 coverage)',
         status='done', evidence='REPORT_part3.md', n_evidence_files=1,
         reason_or_impact=('brief §14 要求的第三份; 含 L 主表 3072 / L-X / 新主路线补格 256 / '
                           '成本与容量 / T1-T5 / 验证表 / coverage')),
    dict(brief_section='§7', item='first_look_receipts (首次观察执行凭据)',
         status='done', evidence='first_look_receipts/first_look_receipt.json',
         n_evidence_files=1,
         reason_or_impact=('记录 B 的批准时间/出处/清单 SHA、两段的封存 receipt 与开封后复核、'
                           '10 件产物的 SHA、4 个脚本的指纹、守卫自检结论')),
]


def main():
    p = os.path.join(R, 'coverage.csv')
    d = pd.read_csv(p)
    before = d.status.value_counts().to_dict()
    hit = []
    for item, up in UPDATES.items():
        m = d.item == item
        if not m.any():
            print('  !! 找不到条目: %s' % item)
            continue
        old = d.loc[m, 'status'].iloc[0]
        for k, v in up.items():
            d.loc[m, k] = v
        hit.append((item, old, up['status']))
    d = pd.concat([d, pd.DataFrame(NEW_ROWS)], ignore_index=True)
    d.to_csv(p, index=False)
    print('== coverage.csv 已更新 ==')
    for it, o, n in hit:
        print('  %-44s %s -> %s' % (it[:44], o, n))
    print('  新增 %d 行' % len(NEW_ROWS))
    print('  改前:', before)
    print('  改后:', d.status.value_counts().to_dict(), ' 总行数', len(d))
    still = d[d.status == 'blocked_by_gate']
    print('  仍被闸挡住:', len(still))
    if len(still):
        print(still[['brief_section', 'item']].to_string(index=False))


if __name__ == '__main__':
    main()
