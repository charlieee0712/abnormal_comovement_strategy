#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6h 事前登记 (brief §1.4 / §11)。必须在【首次新收益评价之前】落盘。

内容 = brief §11 全文 (plan §12.4 Q1-Q10 逐字 + 规划补充 Q11-Q13 + 边界全文)
     + 实际时间 + 输入/代码哈希 + 源 ID 映射。
**不改写编号与问题。** 修订另起 preregistration_amend_<日期>.md。
"""
from __future__ import annotations
import os
import sys
import json
import time

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6h_core as H
import e6g_core as G

RES = H.RES

Q = [
    ('Q1', '本轮哪些分类实际改变了母体用途/规则，哪些只是目录标签？', 'plan §12.4 原文'),
    ('Q2', '每个主母体的可改善损益问题是什么，新信息针对哪里？', 'plan §12.4 原文'),
    ('Q3', '同轴替代、独立补充和状态信息的增量是否不同？', 'plan §12.4 原文'),
    ('Q4', '加回的全分布与同人数SWAP是否改善，而不只是救回赢家？', 'plan §12.4 原文'),
    ('Q5', '条件作用是否超出单条件、人数和资本变化，哪些解释仍未排除？', 'plan §12.4 原文'),
    ('Q6', '哪些有道理的联合结构在单项不强时仍有价值，哪些没有？', 'plan §12.4 原文'),
    ('Q7', '固定代表、同机制组合、局部收缩选择各能保留多少对父优势？', 'plan §12.4 原文'),
    ('Q8', '需求映射在不同母体/时代是否需不同角色，哪些不能迁移？', 'plan §12.4 原文'),
    ('Q9', '期限、人数、受限库存与成本使哪一部分改善保留或翻转？', 'plan §12.4 原文'),
    ('Q10', '还有哪些测量未路由、哪些结构未测试，下一轮应追什么，而不是宣布哪一整库饱和？',
     'plan §12.4 原文'),
    ('Q11', '深度斜率翻号能否归到池规模 / 基准 / 离散度 / 腿本身时变？',
     '规划补充。备择四个；读法 = T1 相关 + T3 子样本；'
     '无效果 = 子样本下翻号不变且相关弱 -> "翻号来源不在这四个量"'),
    ('Q12', '绝对人数深度是否消除翻号？',
     '规划补充。读法 = 逐段 Δ vs 百分比深度，PRE/POST 分列；不选生产深度'),
    ('Q13', 'P16 角落峰位置是否稳定且不依赖 2015+16？',
     '规划补充。读法 = 含 / 不含两套同时带 + 峰位置 + mask Jaccard；'
     '无效果 = 不含 2015+16 无同时带正 -> P16 park'),
]

BOUNDARY = """所有截至 2026-03-27 的历史此前用于研究；推导段结果属研究历史，不叫未污染 OOS；
后段是首次观察但研究者知道 regime，不是未触碰样本；E7 是唯一 OOS。
统计量、成本翻转、局部弱段、MCSE、风险画像用于读表，不作自动淘汰门；
未路由不等于无效；每句"无效果"写母体 × 需求 × 角色 × 日期 × 支持 × 成本；
线状态与 v3 由用户定；E7 HOLD。"""

EXTRA = """### 执行端在登记时刻已经知道 / 还不知道的

**已经知道（不得事后假装是预测）**：E6g 三份 REPORT 与 E6g_REVIEW 的全部结论，
包括结构层五子杠杆对母体中位全负、全窗口 vs R2 同时带正 36 格 = 参数角落、
深度斜率在 2019+ 翻号、含冲击最优 H 15–20 而无冲击最优 H=3、缓冲增量来自 gross、
40 键作否决 vs 反向 ≈ 0、T0 输家 35/35 同号、E6f 的 X1 因标志列错位作废。
本轮的路线（七条）正是在看过这些之后选的，所以**推导段的任何结果都不是 OOS**。

**还不知道（本轮首次观察的对象）**：任何受保护对象（NEW40 键 / TCV / JUMP / IND_* /
六类新规则对象）在 2019-2023 与 2024-2026 上的收益、持仓、条件分布或选择结果。
执行端在记录 B 批准前不读取，守卫以代码强制（攻击测试见 checks/guard_attack_tests.json）。

### 本轮不会做的事（事前写死，防事后滑动）

1. 不因推导段收益删 `routed` 行，也不因收益新增未登记的格。
2. 不看 2019-2023 之后再改 2024-2026 的任何格。
3. 不用收益阈值替代记录 B 的人工批准。
4. 不把"未路由"写成"无效"，不把子杠杆级否定写成线级"穷尽 / 到平台 / 饱和"。
5. 不以卡数、描述符数或审计通过数当改善。
6. 不改 I11 / pool0 / clean / 生产 DEV / 生产 H5 / 8bp 主口径 / 生产 v2。

### 无效果的判定形式（事前固定）

每一句"无效果"必须写满六项：**母体 × 需求 × 角色 × 日期区间 × 支持集 × 成本口径**。
只写"某因子无效"或"某类别无效"的句子一律不合格。
"""


def main():
    os.makedirs(RES, exist_ok=True)
    sm = json.load(open(os.path.join(RES, 'source_manifest.json')))
    now = time.strftime('%Y-%m-%d %H:%M:%S')

    L = []
    A = L.append
    A('# E6h 事前登记（preregistration）')
    A('')
    A('**落盘时间（47 本机）**：`%s`' % now)
    A('')
    A('用途：本文件在 E6h **任何新收益评价之前**落盘（brief §1.4）。')
    A('内容是 brief §11 全文：plan §12.4 的 Q1–Q10 **逐字**，加规划 session 补充的 Q11–Q13，')
    A('加边界全文。**编号与问题不改写**；若需修订，另起 `preregistration_amend_<日期>.md`，')
    A('不覆盖本文件。')
    A('')
    A('---')
    A('')
    A('## 1. 必答问题')
    A('')
    A('| 编号 | 问题 | 来源与读法 |')
    A('|---|---|---|')
    for qid, qt, src in Q:
        A('| **%s** | %s | %s |' % (qid, qt, src))
    A('')
    A('问题与交付的映射（brief §13）：')
    A('')
    A('- `REPORT_part1` 答 Q1 / Q2 / Q3 / Q4 / Q5 / Q6 的**推导段**部分与 Q10 初稿')
    A('- `REPORT_part2` 答 Q3–Q8 的**后段**部分与 Q7')
    A('- `REPORT_part3` 答 Q9、Q11–Q13 与 Q10 定稿')
    A('')
    A('---')
    A('')
    A('## 2. 边界（全文）')
    A('')
    for line in BOUNDARY.strip().split('\n'):
        A(line)
    A('')
    A(EXTRA)
    A('---')
    A('')
    A('## 3. 输入指纹（实际字节）')
    A('')
    A('| 输入 | 实际 SHA256 | brief/plan 声明 | 相符 |')
    A('|---|---|---|---|')
    for r in sm['input_fingerprints']:
        dec = (r['declared_sha256'] or '')[:16] or '（未声明）'
        mk = {True: '是', False: '**否**', None: '—'}[r['matches']]
        A('| `%s` | `%s` | `%s` | %s |' % (r['input'], (r['actual_sha256'] or '')[:16], dec, mk))
    A('')
    if sm.get('warnings'):
        A('**WARN（不阻断）**：')
        for w in sm['warnings']:
            A('')
            A('- `%s`：声明 `%s` / 实际 `%s`。%s' % (w['input'], w['declared'], w['actual'],
                                                    w['explain']))
            A('  %s' % w['impact'])
        A('')
    A('---')
    A('')
    A('## 4. 代码与环境指纹')
    A('')
    A('| 组 | 文件数 | 说明 |')
    A('|---|---|---|')
    for g_, note in (('foundation_readonly', '四地基，只读'),
                     ('e6e_frozen', 'E6e，不改'), ('e6f_frozen', 'E6f，不改'),
                     ('e6g_frozen', 'E6g，不改'), ('e6h_new', '本轮新写')):
        A('| `%s` | %d | %s |' % (g_, sm['counts'][g_], note))
    A('')
    e = sm['env']
    A('环境：Python `%s`、numpy `%s`、pandas `%s`、sklearn `%s`、scipy `%s`。'
      % (e['python'], e['numpy'], e['pandas'], e['sklearn'], e['scipy']))
    A('')
    A('git：HEAD `%s`（%s），tracked 改动 %d 项，untracked %d 项（三个 2026-05 `.py` 与'
      ' 七个 `.sh`，不动不 add）。'
      % (sm['git']['head'], sm['git']['head_subject'][:40],
         len(sm['git']['dirty']), len(sm['git']['untracked'])))
    A('')
    A('---')
    A('')
    A('## 5. 源 ID 映射与注册表规模')
    A('')
    A('| 项 | 值 |')
    A('|---|---|')
    A('| U35（E6e 口径：34 自定义+确认键 + `intraday_cvr_1d`） | %d |' % len(H.U35))
    A('| NEW40 | %d |' % len(H.NEW40))
    A('| U74（= U35 ∪ NEW40） | %d |' % len(H.U74))
    A('| 本轮新派生键 | %d：`%s` |' % (len(H.DERIVED), '`、`'.join(sorted(H.DERIVED))))
    A('| 登记总数 | %d |' % len(H.REGISTERED))
    A('| 新规则对象 | %d：`%s` |' % (len(H.RULE_OBJECTS), '`、`'.join(sorted(H.RULE_OBJECTS))))
    A('| **受保护对象（记录 B 前只能跑推导段）** | %d 个键 + %d 类规则对象 |'
      % (sum(1 for k in H.REGISTERED if H.is_protected_key(k)), len(H.RULE_OBJECTS)))
    A('')
    A('核心三腿身份（已按 47 源码核）：')
    A('')
    A('- **K** = `conditional_turnover` = `turnover_rate / (|log(close/lclose)| + 1e-4)`')
    A('- **T** = `turnover_volatility_60d` = `turnover_rate.rolling(60, min_periods=30).std()`'
      '（**水平与不稳定性混合**，不能改名叫"换手水平"）')
    A('- **C** = `CVR_20d` = `((close−vwap)/vwap).rolling(20, min_periods=10).mean()`'
      '（**不是 `cum_return_20d`**）')
    A('')
    A('四个源符号取负的自定义键（`pool_screening_v2.py`，已逐条读源码核实）：')
    A('')
    A('| 键 | 源函数返回 | 源值【高】的经济含义 |')
    A('|---|---|---|')
    A('| `abn_turnover` | `-abn`，`abn = MA20(turnover)/MA120(turnover)`（:205） |'
      ' 换手相对自身 120 日历史更**低**（更安静） |')
    A('| `parkinson_vol` | `-vol`（:190） | 日内高低区间波动更**低**（区间更窄） |')
    A('| `reversal_skip1` | `-ret_neutral`（:161） | 相对同业的过去十日收益更**低** |')
    A('| `cmf_change_neg` | spec lambda `-compute_cmf_change(window_long=10, window_short=5)` |'
      ' 资金流变化更**负** |')
    A('')
    A('T0 的 `pct_*` 列对**源值**取池内分位（`spec_of_key → specF → get_pct_g(direction=\'hi\')`，'
      '已读调用链）。因此 E6g REPORT 与 E6g_REVIEW 里"波动代理互相冲突"是**符号伪象**，'
      '两者都说输家波动**高**；已在 `E6g_REVIEW.md` §Q1 补记（复盘 #33）。')
    A('')
    A('---')
    A('')
    A('## 6. 守卫状态（登记时刻）')
    A('')
    A('- 推导段 = `%s`；后段 = `%s`' % (' / '.join(H.DERIV_SEGS), ' / '.join(H.POST_SEGS)))
    A('- 受保护对象的 `label_end` 上限 = `%s`' % H.PROTECTED_LABEL_END)
    A('- 取数上限 = `%s`（不读 E7）' % H.MARKET_DATA_END_MAX)
    A('- **记录 B 批准状态 = 未批准**（`registration/record_B_approved.json` 不存在）')
    A('- 守卫攻击测试：见 `checks/guard_attack_tests.json`（13 条攻击必须被拒 + 7 条合法路径'
      '必须放行，全过才算既严又不过严）')
    A('')
    A('---')
    A('')
    A('## 7. 本文件的效力')
    A('')
    A('本文件一旦落盘即冻结。此后：')
    A('')
    A('1. 任何新收益评价都在本文件之后发生。')
    A('2. 问题编号与文字不改。需要补问题 → 另起 amendment，写明**补问题时已经看过什么**。')
    A('3. 后段（2019+）的受保护对象结果，只有在 `registration/record_B_approved.json`')
    A('   存在且 `route_id` 在其清单内时才会被计算——这一条由 `e6h_core.guard_h` 代码强制，')
    A('   不依赖执行端自觉。')
    A('')

    txt = '\n'.join(L) + '\n'
    p = os.path.join(RES, 'preregistration.md')
    if os.path.exists(p):
        raise SystemExit('preregistration.md 已存在, 不覆盖 (修订请另起 amend 文件)')
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(txt)
    print('preregistration.md 已落盘: %d 行 / %d 字节' % (len(L), len(txt.encode())))
    print('  时间 %s' % now)
    print('  Q 数 %d (Q1-Q10 逐字 + Q11-Q13 规划补充)' % len(Q))
    print('  记录 B 批准 = %s' % H.load_approval()['loaded'])


if __name__ == '__main__':
    main()
