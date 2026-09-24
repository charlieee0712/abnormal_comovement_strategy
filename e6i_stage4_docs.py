#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6i Stage 4 草稿: candidate_library_update_proposal.md / line_state_proposal.md / park_ledger_delta.md
(brief §9; plan §12.3; 线三态与 park 规则见项目 memory)。数字全部现算 (研究目录 v36 / part2 面板 / C2 汇总);
这三份是执行端草稿, 定案权在规划 session 与用户。否定结果只写"子杠杆 x 适用域"; 不写线级结论用语。"""
from __future__ import annotations
import e6i_boot  # noqa: F401
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6i_core as I

R = I.RES
PRIM = ('primary', 'primary_inverse_mapped')


def fx(x):
    return ('%+.3f' % x) if np.isfinite(x) else 'NA'


def med(g, c):
    return g[c].median() if len(g) else np.nan


def main():
    t0 = time.time()
    P = pd.read_csv(os.path.join(R, 'reports', 'part2_tables', 'descriptor_panel_post.csv'), low_memory=False)
    cat = pd.read_csv(os.path.join(R, 'reports', 'research_catalog_v36.csv'), low_memory=False).set_index('member_id')
    kp = os.path.join(R, 'carried', 'summary', 'C2_children_delta.csv')
    K2 = pd.read_csv(kp, low_memory=False) if os.path.exists(kp) else None
    M = P[~P.companion.astype(bool)]
    s = pd.to_numeric(M.strength, errors='coerce')

    def mem(mid, role='SLOT', alpha_max=0.25, Hmin=10):
        g = M[(M.member_id == mid) & M.direction_role.isin(PRIM) & (M.role == role) & (s <= alpha_max) & (M.H >= Hmin)]
        return g

    def impact(g):
        if K2 is None or not len(g):
            return 'C2 未就绪'
        k = K2[K2.descriptor_id.isin(g.descriptor_id)]
        c = 'd_net8_minus_sqrt_A5_k0.5'
        if c not in k.columns or not len(k):
            return 'C2 无对应行'
        return '含冲击（A5 亿 κ.5）各段中位 ' + ' / '.join('%s %s' % (s_, fx(v_)) for s_, v_ in k.groupby('segment')[c].median().items())

    short = [('K_samt20', 'SLOT', 'K 腿（部分混入，FALLBACK）', '单位成交额的价格响应（成交吸收 vs 推价）'),
             ('K_amt20', 'SLOT', 'K 腿（部分混入，FALLBACK）', '单位成交额的价格响应'),
             ('K_slope20', 'SLOT', 'K 腿（部分混入，FALLBACK）', '价格对换手的响应斜率'),
             ('K_MA3_E6F', 'SLOT', 'K 腿（部分混入，FALLBACK）', '原 K 的 3 日平滑（E6f 源桥；旧信息的平滑版本，不是新信息）')]
    tnote = []
    for mid in ('T_std20', 'T_mad20', 'T_iqr20'):
        g = mem(mid, 'SLOT')
        tnote.append('%s %s / %s' % (mid, fx(med(g, 'p1')), fx(med(g, 'p2'))))
    L = ['# E6i candidate_library_update_proposal（执行端草稿；定案权在规划 session 与用户）\n',
         '**提案：生产候选库本轮不加任何对象**（U34 / U35、生产 v2、v3 展示候选不改；入地基由用户另定）。理由：后段首次观察把推导段的主要正结果 K 槽位（推导 NW 区间排除 0：正 736 / 负 0）缩到接近 0'
         '（2019-23 小正、2024-26 为负）；11 条路线里 9 条推导合并与后段合并中位都为负（part3 §1）；按"采纳只在 OOS + 用户过目"的规则，本轮没有对象满足采纳条件。\n',
         '另提一个 **E7 事前登记短名单（研究候选，不是生产候选）**：从"推导与后段中位都为正、且对匹配随机后段为正"的成员里，按族事前固定、每项只登记一个中间档配置'
         '（小 α、长 H），E7 开启时作为首次 OOS 观察对象。成员是按两期结果筛出的，有选择偏差——这正是需要 E7 的原因。\n',
         '| 成员 | 改善对象 / 角色 | 母体 | H · 成本 | 增益来源 | 证据（主方向单成员描述符中位；年化百分点） | 时间与风险范围 | 剩余不确定性 | 所需后续验证 |',
         '|---|---|---|---|---|---|---|---|---|']
    for mid, role, obj, src in short:
        if mid not in cat.index:
            continue
        c = cat.loc[mid]
        g = mem(mid, role)
        L.append('| %s | %s | %s | H ≥ 10；8bp（%s） | %s | 推导 %s / 后段 %s / 四段 %s；后段 NW 排除 0 正 %d 负 %d；对匹配随机后段 %s；本表配置（α ≤ .25、H ≥ 10）%d 个，后段两段中位 %s / %s | '
                 '2024-26 K 路线整体为负（2024 最差）；K 与换手水平同源，拥挤 / 流动性冲击时可能同向失效 | 新信息 vs 给 K 同向加权未分离；成员由两期结果筛出 | '
                 'E7 事前登记（本表配置、按族固定）；新旧排序分歧分层；含冲击口径 |' % (
                     mid, obj, '、'.join(sorted(g.mother_id.unique())) or 'R1 / R2 / A06', impact(g), src,
                     fx(c.deriv_median), fx(c.post_median), fx(c.all4_median), int(c.post_ci_pos), int(c.post_ci_neg),
                     fx(c.zmap_post_median), len(g), fx(med(g, 'p1')), fx(med(g, 'p2'))))
    L += ['',
          '**同对象多支**：K 腿的四个成员互为替代（同一槽位同一时刻只混入一个），不叠加；保留多支是为了在 E7 里区分"响应族整体"与"平滑的原 K"（K_MA3）两种解释，'
          '避免把旧信息的平滑当作新测量的功劳。\n',
          '**不进短名单但保留在研究目录的**：T 的 20 日绝对尺度成员（成员层两期中位为正，但在短名单同一配置 SLOT FALLBACK α ≤ .25、H ≥ 10 下两后段中位为 %s——'
          '2024-26 为负或接近 0，证据不足）；C 的 40 日成员（只后段为正）；V_idio20（只后段为正）；K_rar 的竞争方向（需要重新登记方向）；四臂组合（交互为正来自亏损不叠加）。\n'
          % '；'.join(tnote)]
    open(os.path.join(R, 'reports', 'candidate_library_update_proposal.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    # ---------------- 线状态提议 ----------------
    def rt(r, **kw):
        g = M[M.route_id == r]
        for k_, v_ in kw.items():
            g = g[g[k_].isin(v_ if isinstance(v_, (list, tuple)) else [v_])]
        return '推导 %s / 后段 %s（%d 个描述符）' % (fx(med(g, 'deriv')), fx(med(g, 'post')), len(g))
    LS = ['# E6i line_state_proposal（执行端草稿；状态由用户定，规划 session 复核）\n',
          '规则：一轮只移一级；headline 不能直接 park；否定只写"子杠杆 x 适用域"；从未测 ≠ park。\n',
          '**E6i proposal 事前登记的降级条件**："八族推导段测量级全部 |ρ| ≤ 0.08 **且** 角色级对同人数核心中位 ≤ 0 → 下轮转 carried"。'
          'K 槽位（主方向 + 部分混入，1134 个描述符）推导段对同人数核心中位 +0.187 / +0.379（part1a〔Q2-OBJ〕）→ 后半不成立 → 条件未触发；'
          '因此线本身提议保持 headline、按后段结果收窄。\n',
          '下表"（新）→ park"的行是 headline 线内本轮首次测的**子杠杆 x 域**（不是线）：按 park 台账规则登记否定范围、触发条件与重测内容'
          '（同 E6h 的 P20 / P21 先例）；线的状态只按一轮一级移动。\n',
          '| 线 / 子杠杆 | 本轮证据 | 上轮状态 | 提议状态 | 升降条件 |', '|---|---|---|---|---|',
          '| 因子端迭代（八族估计量 x 策略适配） | 八轴 276 个目录成员（记录 B 解封 236 个）；35,384 个主描述符推导与后段两期全跑；成员层两期为正的 11 个成员都在 K（响应族与源桥）与 T（20 日绝对尺度）两轴（part3〔P3-BOTH〕） | headline | **headline（收窄）** | '
          '收窄到 K / T 两族的构造细化（新旧排序分歧分层、水平匹配后的离散、长 H）与 E7 事前登记准备；若下一轮细化后仍无后段可分辨的增量 → carried |',
          '| K 响应族（SLOT 部分混入） | %s | （新） | 留在 headline 子线 | 见候选库提案短名单 |' % rt('RK', direction_role=list(PRIM), policy='FALLBACK'),
          '| T 小权重加 / 20 日复合 | 小权重 %s；复合 TPAIR %s | （新） | 小权重留 headline 子线；复合 → park（P31） | 水平匹配离散登记后重测复合 |' % (
              rt('RT', direction_role='primary', policy='FALLBACK'), rt('TPAIR')),
          '| V 保留集删除 | %s | （新） | park（P26） | 事前登记的市场状态条件 |' % rt('RV', direction_role='primary'),
          '| O 保留集删除 / 跳空焦点 | %s | （新） | park（P27） | 正向用途（保留条件 / 腿）事前登记 |' % rt('RO'),
          '| R 同人数 SWAP（同业相对） | %s | （P21 触发重测） | park（P28；P21 维持 park） | 改作槽位内分量 |' % rt('RR', role='SWAP'),
          '| A 同预算换入 | %s | （新） | park（P29） | 新的事件时钟测量 |' % rt('RA', role='SWAP'),
          '| S 状态内条件换入 | %s | （新） | park（P30） | S 改作槽位权重的条件 |' % rt('RS', role='SWAP'),
          '| C 核心槽位（A06）/ CVR 焦点替换 | 槽位 %s；焦点替换 %s | （新） | 槽位 carried（后段非负、低优先级）；焦点替换 park 维持原 CVR_20d | 槽位在其他母体可登记时重测 |' % (
              rt('RC', direction_role='primary', role='SLOT'), rt('RC', direction_role='primary', role='FOCAL_NEW')),
          '| 摩擦边缘替换（RL） | %s | （新） | park（P33） | κ 校准或可成交数据 |' % rt('RL'),
          '| M2 形状校准 | 两期对母体接近 0；零修改的 (程序 x 年) 占比后段 46% / 77% | （新） | park（P32） | 事前固定形状的角色（Q17） |',
          '| 池子扩张分离（C1） | 见 part3 §2 | carried | carried（结论见 part3，交规划 session 定） | — |',
          '| 成本 / 持有期（C2 冲击透镜） | 见 part3 §3 | carried | carried | κ 校准 |',
          '| 信号线（C3 描述） | R0 §9 | carried（零算力） | carried | 另立对象与授权 |', '']
    open(os.path.join(R, 'reports', 'line_state_proposal.md'), 'w', encoding='utf-8').write('\n'.join(LS) + '\n')
    # ---------------- park 台账增量 ----------------
    PK = ['# E6i park_ledger_delta（执行端草稿；编号接 E6h REVIEW 的 P20–P25；定案权在规划 session 与用户）\n',
          '每条：适用域 + 触发（恢复）条件 + 事前登记的重测内容 + 读法基准；恢复 ≠ 采纳。\n',
          '| 编号 | 结论（子杠杆 x 适用域） | 本轮证据 | 触发条件 | 重测内容（事前登记） | 读法基准 |', '|---|---|---|---|---|---|',
          '| P26 | V 保留集无条件删除 / 缩减 x R2 / A06 x 2010-2026 x 8bp | %s；同资本接近 0；2024-26 反向删除为正 | 事前登记的市场状态条件 | 状态内 V 删除 VETO k{5,10} / SOFT λ{.5} | 同资本 + 反向同 m |' % rt('RV', direction_role='primary'),
          '| P27 | O 保留集删除与跳空焦点状态 x R1 / R2 / A06 x 2010-2026 | %s | 正向用途（保留条件 / 腿）登记 | 高跳空保留条件 x H{3,5} | 同资本 + 反向 |' % rt('RO'),
          '| P28 | 同业相对位置作同人数 SWAP x R1 / R2 / A06 x q{.05,.1,.2} x 2010-2026 | %s；对匹配随机后段为负 | 改作槽位内分量 | K / T 槽位内部分混入 α{.125,.25} | 匹配随机（沿 P21 原主读数） |' % rt('RR', role='SWAP'),
          '| P29 | A 事件基线成员作同预算换入（两种换出规则）x R1 / R2 / A06 | %s | 新的事件时钟测量 | 新测量作换入 q{.1} | 匹配随机 |' % rt('RA', role='SWAP'),
          '| P30 | S 状态内按 R_peer20 条件换入 x R1 / R2 / A06 | %s；后段对匹配随机为负 | S 改作槽位权重条件 | 状态条件 x K 槽位 α | 匹配随机 + 反向 |' % rt('RS', role='SWAP'),
          '| P31 | T 腿改为 level x CV 复合（TPAIR）x 四母体 | %s | 水平匹配后的离散测量登记 | 复合 β{.25,.5} | 同人数核心 |' % rt('TPAIR'),
          '| P32 | M2 低维形状校准（[u, u², u·z]）x 代表 x 四母体 | 两期对母体接近 0；后段零修改 46% / 77% 的 (程序 x 年) | 事前固定形状角色 | 固定 U 形 / 单边 x SLOT | 同 H 母体 + 同预算 M0 |',
          '| P33 | 摩擦边缘替换（RL）x R2 / A06 | %s | κ 校准或可成交数据 | RL 含冲击口径 | 独立源成本 net + gross 拆分 |' % rt('RL'),
          '',
          '**触发项的重测结果（E6i proposal §3 触发的 P4 / P12 / P18 / P20 / P21 / P22）**：',
          '- P20（T 测量部分混入，读法基准 = 同人数核心）：后段 T 腿完全替换对同人数核心两段为负；小权重加后段接近 0 → **维持 park**（域补 2019-2026）。',
          '- P21（同业相对位置，读法基准 = 匹配随机）：RR 同人数 SWAP 后段对匹配随机两段为负；ADD 接近 0 → **维持 park**，"画像级保留"在 SWAP 算子上后段不成立。',
          '- P22（隔夜跳空的反向读法）：O 的删除角色两期为负、正向保留角色本轮未单独登记 → **维持 park**。',
          '- P4（相对自身水平的活动量作 K 族成员）：K_rar 登记主方向两期为负、竞争方向推导段与 2019-23 为正 → 方向需重新登记（新对象），P4 维持 park 并记方向线索。',
          '- P12（R 族 skip / 窗 / 行业内排序变体）：R 路线的 SWAP 与 ADD 两期多为负 → 维持 park。',
          '- P18（第四腿用定向造的新测量）：ADD_SCORE（小权重加）在 V / R 两期多为负 → 维持 park。', '']
    open(os.path.join(R, 'reports', 'park_ledger_delta.md'), 'w', encoding='utf-8').write('\n'.join(PK) + '\n')
    for fn in ('candidate_library_update_proposal.md', 'line_state_proposal.md', 'park_ledger_delta.md'):
        txt = open(os.path.join(R, 'reports', fn), encoding='utf-8').read()
        for b in ('可交付', '已确证', '必须换核', '饱和', '穷尽', '到平台'):
            if b in txt:
                raise SystemExit('%s 含禁用词 %s' % (fn, b))
    print('stage4 docs 写出; %.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
