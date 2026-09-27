# -*- coding: utf-8 -*-
"""E6j Stage A：P / B 两个登记包同时冻结（brief v1.2 §1.4 / §3 / §7 / §12；plan §10.2）+ 记录 B 事前整表授权文件。
在任何新收益读取之前运行；只写 registration/。修订另起 preregistration_amend_<日期>.md，不改编号与问题。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import time
import subprocess

import pandas as pd

import e6j_core as J

REG = os.path.join(J.RES, 'registry')
OUT = os.path.join(J.RES, 'registration')
PLAN_LINES = dict(s4='216–317', s5='319–474', s6='477–518', s7='521–601', s8='605–683', s9='687–792', s510='450–469', s41='218–234',
                  s45='280–315')

# 假设模板 v2（proposal 附录 B）十项：① 机制 ② 方向论证 ③ 最强处 ④ 竞争解释 + 判别列 ⑤ 资本中性角色 + 事前主配置
# ⑥ 一致性判据 + 功效 + 零期望 ⑦ 结构转移预测 ⑧ 采纳路径 ⑨ 无效果 / 反向读法 ⑩ 登记单位
T = {
 'Q01': ['身份问题（非经济机制）：A4b_CVRv5 与 R1 是否同一对象、试点 S / M / C1 是否已在 E6i 见过', '不适用；S / M / C1 方向沿登记',
         '—', '完全别名 / 母体同但 SLOT 实现不同 / 支持或费用差造成汇总巧合；判别列 = 掩码 / 权重 / 持仓 / 日账本四层 + SLOT 逐格（Stage 0 已答：exact_alias + SLOT 逐格同）',
         '不适用', '四层逐位（数值容差按输入尺度，不抄 1e−15）；零期望 = 身份恒等', '其余五形态非别名 → 提供转移证据',
         '别名对象读数标 historical_exposed / alias_of，不作独立证据', 'exact alias → 复现与政策应用；实现差 → 算法转移；不同结构 → 有界转移', '描述符（形态 × 臂 × α × H）'],
 'Q02': ['S = K0 / b = a × q：候选机制 = 低历史活动 b / 高相对放量 a / 价稳 q / a×q 交互', '按 B1 表逐成员（主方向 + 命名竞争反向）；S 方向为 E6i 对照方向事后转正（已暴露）',
         '同 K 层边界编辑处；短 H（H3–H5）；不预设母体', 'b 即可解释 → 简化候选；a×q 独有 → 条件表达；仅覆盖 / 资本 → 实施差；SRC 与 TRANSPORT 分歧 → 秩坐标；判别列 = 同槽位分量账户、b / a / q 三分位与 3×3 表、编辑资本、粗风格条件随机',
         '主配置 α .25 × H5 FALLBACK native；同资本并列', '研究块不设门；报点估 / HAC 区间 / MDE80 = 2.80·SE；identity 为真零、MA3 为主动基线',
         'R1 / R2 / A06 分别报，不预设同号', '简化候选进后续清单，不替换 P 主对象', '均弱 → 只否定当前角色；反向更好 → 按竞争方向读、登记暴露', '测量 × 方向 × 母体 × α × H'],
 'Q03': ['滚动基线可能把事件自身吸收进常态；事件前冻结 / 60 日基线含义更稳', 'rarpre 低坏（与 S 同向）为主、反向为竞争；R_ev / U 两向分别登记',
         '重复触发 / 持续 spell、事件日龄短处', '覆盖差（更常有值）/ 时钟差 / 响应差逐项分开；判别列 = W20 vs W60、last_trigger vs spell、原 K 共同支持、实际持有路径',
         '主配置 α .25 × H5；COMMON_SUPPORT 四账户', '同 Q02', '分母体报', '适配的时间尺度写入下一次测量合同', '事件版不必胜；无差 → 时钟不是瓶颈', '测量（窗 × 时钟）× 方向 × 母体 × α × H'],
 'Q04': ['β = ρ · s_y / s_x：M 优于均值可能来自 ρ（协动）或尺度', 'β_norm / ρ 主方向与 M 同（高好）；scale 两向',
         '波动分化大的年份（E6i 近段）', 'ρ 仍有增量 → 协动；尺度 → 风险 / 活动测量；只原 M 好 → 交互；判别列 = β、ρ、尺度比、β·x̄/(ȳ+ε)、MA3 同槽位',
         '同 Q02', '同 Q02', '分母体', '选更合适估计而非强删有效尺度；不称 β 因果弹性', '全弱 → 当前构造无增量', '测量 × 方向 × 母体 × α × H'],
 'Q05': ['20 日 OLS 可能由少数日期控制；按留一稳定性收缩可减少噪声编辑', '原 M 方向（低坏）；只在 qM 与 q0 之间收缩',
         '高换手成本处', '只是总剂量下降 → COMMON-DOSE 同平均 r 对照；r 与股票对应 → r-shuffle；判别列 = 有效 α 分布、边界变更数、成本差',
         '主配置 α .25 × H5；剂量控制同批', '同 Q02', '分母体', '降成本即实施改善；不自动搜索更多收缩函数', 'gross 更好不增成本更直接；相抵则如实记', '可靠性成员（CC / ID）× 母体 × α × H'],
 'Q06': ['MA3 的价值可能来自降噪，也可能来自保留量价协动（mean ratio ≠ ratio of means）', 'Q_λ 高坏；COV/P 两种解释分别登记',
         '—', 'λ = 1 闭合（恒等）；λ0 更好 → 协动噪声应抑制；中间最好 → 折衷待验；判别列 = 完整分解、同窗同单位、正反角色',
         '同 Q02', '同 Q02；λ = 1 ≡ MR 为恒等锚', '分母体', '以实际账户与成本选下一步', '无差 → 分辨不出', '测量（λ × 价格 × 窗）× 方向 × 母体 × α × H'],
 'Q07': ['S 与 M 可能解决不同问题；年度代理相关 0.38 不构成互补证明', 'SM = 两分量各 α/2（S 低坏、M 低坏）；分量各自回退',
         'K 边界处', '正交互 + AB 仍负 → 亏损次可加；AB 正但不超单臂 → 不需复杂化；判别列 = 半剂量四臂 I = V(S.125,M.125) − V(S.125,0) − V(0,M.125) + V(0,0)、同总剂量单臂、分别打乱 S / M、共享 donor 随机',
         '主配置 α .25（分量 .125）× H5', 'P 政策六条 + 三句加法（SM 取代最佳合格单臂须合并差 ≥ +.10）', '六形态各自计分', '《生产变更候选清单》，deployment_authorized = false',
         '交互 ≤ 0 → 说明抵消发生在哪（量价信息 / K 边界 / 交易抵消）', '形态 × 臂 × α × H'],
 'Q08': ['排名分歧大 ≠ 新信息；可能只是边界编辑强度', '不适用（编辑账本）', '大分歧层', '编辑强度匹配后仍有差 → 新增决策内容；差消失 → 重排规模；判别列 = 边界距离 × 分歧 × 编辑资本、实际 Δ 权重、EDIT-ENTRY / EDIT-BOTH、粗风格随机',
         'P 四个非恒等主对象 + B 的 S / M / MA3 主配置', '描述性；不设门', '分形态', '不从"分歧无关"推出"只是加权"', '无法匹配 → 未识别', '主对象 × 编辑层'],
 'Q09': ['A4b 的 K 改变会改第二关 T 的回归样本；子 − 母含 K 直接编辑与 T 重估', '不适用', 'A4b / A4b_CVRv5',
         '判别列 = V00 / V10 / V01 / V11 双开关顺序平均（算法作用分解，非经济中介）', 'P 主配置 × A4b 两形态 × 四臂', '描述性', '—', '下一次母体需求表标明第二关放大 / 抑制', 'T 贡献大 ≠ K 信息不存在', '形态 × 臂（主配置）'],
 'Q10': ['日内 |r_id| 可能更贴成交响应；CC / ON 也可能保留预测信息', 'POINT / MR / ROS 高坏、SLOPE 高好；反向为命名竞争',
         '隔夜份额高、价格限制附近', '测量优 ≠ 账户优；ON 有效不证明冲击；判别列 = ID / CC / ON / range 单一坐标配对、cancel、overnight_share、T→T+1 不可捕获区间',
         '同 Q02', '同 Q02', '分母体', '"预测信息"与"冲击估计"角色分开', 'ID 弱不否定作者结论', '测量（单位 × 价格 × 聚合）× 方向 × 母体 × α × H'],
 'Q11': ['I11 条件纯多头短持有下，下跌日承接与下跌冲击 / 风险补偿方向可能相反', 'K_up / K_dn 两向分别登记（承接 vs 风险补偿）；asym 两向',
         '零收益 / 价格限制日多的票', '判别列 = CC / ID、up / down / zero、ROS / MR、频率贡献、反向', '同 Q02', '同 Q02', '分母体',
         '指定分支更好只限方向 × 母体 × 成本', '两方向均弱 → 不生造不对称故事', '测量 × 方向 × 母体 × α × H'],
 'Q12': ['事件后再估基线会吞掉异常；1–2 日事件窗噪声大', 'rarpre / R_ev / R_ev5 / U 两种解释分别登记', '事件日龄短、重复触发',
         '时钟差 / 覆盖差 / 响应差逐项分开；判别列 = 原 R_ev、m5 收缩、U、rarpre、源滚动；W20 / 60；两事件时钟', '同 Q02', '同 Q02；R_ev 常数比例过程 ≡ 1 为恒等锚', '分母体',
         '信号来自重复触发则记录，不追认新事件', '随机无效过程 R_ev 中位偏移不是 bug', '测量 × 方向 × 母体 × α × H'],
 'Q13': ['同一测量在三种核心结构（序贯 / 均值 / 交集）的边际不同', 'P 五臂方向沿登记', '取决于 K 在何处成为绑定约束',
         '判别列 = 六形态同对象主配置、K 边界编辑、行业 cap、T-refit', '主配置 α .25 × H5', '各形态单独计分；一个形态通过仍是局部候选', '不预定序贯 > 均值 > 交集',
         '建立"测量—绑定环节"地图', '只一个形态通过 → 局部候选；其余五形态不作一致性硬门', '形态 × 臂 × α × H'],
 'Q14': ['T 的自身归一与去趋势不是同义；peer 只有在 K / T 边界才可能有用', 'B6 高坏主、反向竞争；B7 相对同业落后为主', '分母体（A08 只参加 B6）',
         '判别列 = B6 各测量与源 T、B7 K / T 分域、同 N、随机', '同 Q02', '研究块无门', '分母体、分槽位', '只作研究清单，不晋升本轮五臂', '角色失败不外推全因子', '测量 × 方向 × 槽位 × 母体 × α × H'],
 'Q15': ['投资规模不是中性背景：部分收益差随资本缩减改变', '不适用', '资本差大的形态', '判别列 = NATIVE / MATCH-CAP / ATTRIBUTION 三视图、共同支持、线性费用与冲击分模型、库存影子账户',
         'P 全网格；carried C1 N×B', '同资本符号比较按 FULL；逐段同号只诊断', '—', '账户目标 / 容量情景写入下轮问题', '原生好而同资本差 → 资本 / 风格贡献明显', '形态 × 臂 × α × H × 资本视图'],
 'Q16': ['用户要小且可能有用的改进不被低功效无限搁置，同时不能事后挑格过线', 'P 主对象冻结', '—',
         '主动 MA3、机会基线（随机通过率）、δ 敏感、MC 误差、历史选择暴露；FULL / G4 与随机主参照先于结果锁定、不交叉拼接',
         '主配置 α .25 × H5；policy_aggregation = FULL_E6I_ALL4；random_ref = R-MATCH-SRC；capital_ref = same_capital', '六条 + 三句加法（δ = .10，敏感 .05 / .15）；不以显著性为门槛',
         '六形态各自计分', '通过 → 《生产变更候选清单》四标签分开（policy_score / mechanism_status / replication_status / deployment_authorized = false）',
         '边缘性高 → 报具体哪条与效应尺度，不改 δ / 年份分母 / 参考母体', '形态 × 臂（主配置）'],
 'Q17': ['元问题：本轮是否改进了假设形成方法', '不适用', '—', '每 Q 的证据、前提、竞争解释、对照、结论域、真实结果是否一一对应', '不适用', '不以命中率打分',
         '—', '每项交 hypothesis_update_card 八字段', '设计错误 / 正常证伪 / 未覆盖 / 低精度 / 新线索分别记录', 'Q 卡'],
}
TPL_COLS = ['① 机制', '② 方向论证', '③ 最强处', '④ 竞争解释 + 判别列', '⑤ 资本中性角色 + 事前主配置', '⑥ 一致性 / 功效 / 零期望', '⑦ 结构转移预测',
            '⑧ 采纳路径', '⑨ 无效果 / 反向读法', '⑩ 登记单位']
P_QS = ('Q01', 'Q02', 'Q07', 'Q13', 'Q15', 'Q16')

PROCESS_EXPOSURE = [
    ('EX-01', 'S 方向', 'E6i 对照方向（K_rar20 低坏）事后转正为本轮主方向（direction_2of1），不是未见数据的首次预测', 'P S / SM；B1 S_source'),
    ('EX-02', 'S / M / C1 选材', '来自 E6i 已看过四段的事后回扫（supplement 1 / 2）', 'P 全部臂；B 对应源成员'),
    ('EX-03', '主母体', 'A4b_CVRv5 ≡ R1 exact_alias：主母体上 S / M / C1 与 K_rarpre / K_samt20 全网格 = E6i 已跑账户（alias_of）', 'P 主母体 60 个描述符'),
    ('EX-04', 'α / H 网格与主配置', 'P 网格与 E6i 同；主配置 .25 × H5 由用户在看过 E6i 后定', 'P 全部'),
    ('EX-05', '政策', '六条 + δ = .10 于 2026-09-25 在看过 E6i 结果后形成（RULING 第 15 项）；三句加法见 proposal §5.1', 'P 政策评分卡'),
    ('EX-06', 'B 块设计', 'B1–B7 的问题部分由 E6i 事后诊断（supplement 2：水平 vs 异常、平均 vs 边际）启发', 'B 全部'),
    ('EX-07', '特殊年份', '去 2015+2016、去 2020 的删年版本来自历史已暴露问题，不是新随机样本', '稳健性表'),
    ('EX-08', 'T_ewcv20 / amount 族', 'T_ewcv20 在 E6i α .25 × H5 通过六条；amount 族四段结果已见', 'B6 源成员；P 列对象'),
]


def sha_map(files):
    return {f: J.sha_file(os.path.join(REG, f)) for f in files}


def tpl_table(qs):
    lines = ['| Q | ' + ' | '.join(TPL_COLS) + ' |', '|' + '---|' * (len(TPL_COLS) + 1)]
    for q in qs:
        lines.append('| %s | ' % q + ' | '.join(c.replace('|', '/') for c in T[q]) + ' |')
    return '\n'.join(lines)


def main():
    os.makedirs(OUT, exist_ok=True)
    now = time.strftime('%Y-%m-%d %H:%M:%S')
    head = subprocess.run(['git', '-C', J.CODE, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    a0 = json.load(open(os.path.join(REG, 'a0_manifest.json')))
    if not a0['all_pass']:
        raise RuntimeError('A0 编译未全过，不得登记')
    sm = json.load(open(os.path.join(J.RES, 'source_manifest.json')))
    if not sm['stage0_all_pass']:
        raise RuntimeError('Stage 0 未全过，不得登记')
    code = {f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_core.py', 'e6j_prod.py', 'e6j_slot.py', 'e6j_features.py', 'e6j_random.py', 'e6j_a0.py')}
    P_files = ['descriptors_P.csv', 'cs_P.csv', 'controls.csv', 'exposure_ledger.csv', 'a0_manifest.json']
    B_files = ['rows_B.csv', 'descriptors_B.csv', 'cs_B.csv', 'controls.csv', 'question_to_objects.csv', 'task_to_objects.csv', 'a0_manifest.json']
    common = dict(written_at=now, git_head=head, plan_sha256=J.sha_file(os.path.join(J.RES, 'PLAN_COPY.md')),
                  brief_sha256=J.sha_file(os.path.join(J.RES, 'brief_copy.md')), code_sha256=code, policy_locks=a0['policy_locks'],
                  grids=a0['grids'], stage0_manifest_sha256=J.sha_file(os.path.join(J.RES, 'source_manifest.json')))
    import glob
    p_members = ('K_rar20', 'K_slope20', 'K_MA3_E6F', 'K_rarpre', 'K_samt20', 'K_amt5', 'K_samt5', 'K_amt20')
    e6i_mem = {'%s/%s' % (s, m): json.load(open(os.path.join(J.E6I_RES, 'cache', s, '%s__OBS.json' % m)))['sha256']
               for s in J.SEGMENTS for m in p_members + ('T_ewcv20', 'R_peer20')}
    j_mem = {'%s/%s' % (os.path.basename(os.path.dirname(p)), os.path.basename(p)[:-5]): json.load(open(p))['sha256']
             for p in sorted(glob.glob(os.path.join(J.RES, 'cache', '*', 'J_*.json')))}
    Pm = dict(package='P', registry_sha256=sha_map(P_files), counts=dict(P=a0['counts']['P'], CS_P=a0['counts']['CS_P']),
              member_cache_sha256={k: v for k, v in e6i_mem.items() if k.split('/')[1] in p_members}, **common)
    Bm = dict(package='B', registry_sha256=sha_map(B_files), counts=dict(rows=a0['counts']['rows'], B_per_segment=a0['counts']['B_per_segment'],
                                                                          CS_B=a0['counts']['CS_B'], blocks=a0['counts']['blocks']),
              member_cache_sha256=dict(e6i=e6i_mem, j=j_mem), **common)
    J.atomic_write_json(os.path.join(OUT, 'P_package_manifest.json'), Pm)
    J.atomic_write_json(os.path.join(OUT, 'B_package_manifest.json'), Bm)
    B_manifest_sha = J.sha_file(os.path.join(OUT, 'B_package_manifest.json'))
    # 暴露台账（过程级 + 描述符级）
    ex = pd.DataFrame(PROCESS_EXPOSURE, columns=['exposure_id', 'what', 'detail', 'scope'])
    J.atomic_write_csv(os.path.join(OUT, 'selection_exposure_ledger.csv'), ex)
    exd = pd.read_csv(os.path.join(REG, 'exposure_ledger.csv'))
    rows = pd.read_csv(os.path.join(REG, 'rows_B.csv'))
    locks = a0['policy_locks']
    lock_txt = ('`policy_aggregation = %s`（W07：E6i `descriptor_stats_all4` 四段按有效日合并；G4 = 四段增量中位并印）；`random_ref = %s`（W08：匹配条件 = Z-MAP basic，'
                '种子按 plan §8.2 稳定哈希重做）；`capital_ref = %s`（W09：逐形成日共同资本只缩不放、完整重跑）；δ = %.2f（敏感 %s）；'
                '`policy_confirmation_status = %s`（W12）；主配置 α %.2f × H%d；成本 %.0fbp。') % (
        locks['policy_aggregation'], locks['random_ref'], locks['capital_ref'], locks['delta'], ' / '.join('%.2f' % x for x in locks['delta_sensitivity']),
        locks['policy_confirmation_status'], locks['main_config']['alpha'], locks['main_config']['H'], locks['cost_bp'])
    # ---- P 包
    p = ['# E6j preregistration_P —— 冻结五臂试点（P 包）', '',
         '用途：P 包事前登记（brief v1.2 §1.4 / §12；plan §10.2）。在任何新收益读取之前落盘；修订另起 `preregistration_amend_<日期>.md`，不改编号与问题。',
         '写入 %s（47 时间）；HEAD `%s`；PLAN_COPY.md sha256 `%s`；brief sha256 `%s`；P 包清单 `registration/P_package_manifest.json`。' % (now, head[:7], common['plan_sha256'][:12], common['brief_sha256'][:12]), '',
         '## 1. 设计全文（逐字引用，不转录）',
         '- plan §4（`PLAN_COPY.md` 第 %s 行）：统一评分符号与缺失、有效域与秩坐标（§4.1a）、三种母体接入（§4.2）、主对象与网格计数（§4.3）、剂量互补（§4.4）、政策计算合同（§4.5，第 %s 行）。' % (PLAN_LINES['s4'], PLAN_LINES['s45']),
         '- plan §9 Q 卡（`PLAN_COPY.md` 第 %s 行）中 %s 逐字适用于本包。' % (PLAN_LINES['s9'], ' / '.join(P_QS)), '',
         '## 2. 锁定值（登记前锁，不 PENDING）', lock_txt, '',
         '## 3. 对象',
         '- 五臂：C0 = 恒等（显式短路）；S = K_rar20（低坏）；M = K_slope20（低坏）；SM = 两者各 α/2（分量各自回退）；C1 = K_MA3_E6F（高坏）。'
         '列对象：K_rarpre（低坏）、K_samt20（低坏）、AMT4 = K_amt5 / K_samt5 / K_amt20 / K_samt20 四分量各 α/4（低坏，分量各自回退；SM 规则的推广，设计选择）。',
         '- 成员原值 = E6i 缓存（sidecar sha 校验；Stage 0 T7）；生产坐标 pct 与 E6i NS 表逐位（Stage 0 T6）。',
         '- 接入（W05）：A4b 混合 pct 进第一关；Mmean_v2 替换 pcond；Munion_v2 替换 cond 剔尾集；CVRv5 否决不变。',
         '- 计数：主五臂 312 + 列对象 216 = **528**（`registry/descriptors_P.csv`）；COMMON_SUPPORT 子 / 父 192（`registry/cs_P.csv`）；控制分表见 `registry/controls.csv`。',
         '- 主决策表：4 个非恒等臂 × A4b_CVRv5 × α .25 × H5；其余五形态分别计分；全网格标明探索、不进结论句。', '',
         '## 4. 暴露（selection_exposure_ledger）',
         '- 过程级：`registration/selection_exposure_ledger.csv`（%d 条）。' % len(ex),
         '- 描述符级：`registry/exposure_ledger.csv` —— %s。' % '、'.join('%s %d' % (k, v) for k, v in exd.exposure_type.value_counts().items()),
         '- **主母体上 S / M / C1 与 K_rarpre / K_samt20 的全网格 = E6i R1 SLOT 账户的精确别名（四段均已见）**：这些描述符按 alias_of 复用 E6i 身份、仍在生产路径重算作交叉核对；政策读数照算，但标 historical_exposed，不作独立证据。', '',
         '## 5. 问题卡（假设模板 v2 十项）', tpl_table(P_QS), '',
         '## 6. 执行', '- P 登记落盘后六形态四段一次算完（不是 OOS；登记的意义是钉判据），封存回执后按清单读；不存在"读完主母体再改其他形态对象"的分支。']
    J.atomic_write_text(os.path.join(OUT, 'preregistration_P.md'), '\n'.join(p) + '\n')
    # ---- B 包
    bl = rows.groupby('block').size().to_dict()
    b = ['# E6j preregistration_B —— K 分离研究（B 包）', '',
         '用途：B 包事前登记（brief v1.2 §1.4 / §3 / §12；plan §10.2）。与 P 包同时冻结；推导段先跑；后段按记录 B 事前整表授权（生效条件见 §5）。',
         '写入 %s（47 时间）；HEAD `%s`；B 包清单 `registration/B_package_manifest.json`（sha256 `%s`）。' % (now, head[:7], B_manifest_sha[:12]), '',
         '## 1. 设计全文（逐字引用）',
         '- plan §5（`PLAN_COPY.md` 第 %s 行，含 §5.10 封闭角色清单第 %s 行）、§6（第 %s 行）、§7（第 %s 行）、§8（第 %s 行）、§9 全部 Q 卡（第 %s 行）。' % (
             PLAN_LINES['s5'], PLAN_LINES['s510'], PLAN_LINES['s6'], PLAN_LINES['s7'], PLAN_LINES['s8'], PLAN_LINES['s9']), '',
         '## 2. 网格与计数（编译器现算）',
         '- W10：α ∈ {.125, .25, .5} × H ∈ {1, 2, 3, 5, 10, 15, 20}；210 个 测量—方向—槽位 登记行（%s）；B6 在 R1 / R2 / A06 / A08、其余在 R1 / R2 / A06。' % '、'.join('%s %d' % (k, bl[k]) for k in sorted(bl)),
         '- 每段 **%d** 个原生 FALLBACK 描述符（brief 写 13,230，差 = B6 的 A08；以编译为准）；COMMON_SUPPORT 子 / 父 %d（α .25 × H{3,5,10,20}）；控制分表见 `registry/controls.csv`。' % (a0['counts']['B_per_segment'], a0['counts']['CS_B']),
         '- 两张独立表（问题 → 对象、任务 → 对象）逐元组相等（`registry/a0_manifest.json`）。', '',
         '## 3. 登记行（方向、论证、双向标记、问题卡）', '见 `registry/rows_B.csv`（210 行，逐行含 rationale / direction_role / bidirectional / hypothesis_ids / operator_id）。'
         'K0 锚：J_B2_POINT_TR_CC 高坏 = 母体 K 腿逐位（账户 = 母体，不重复计算，exposure 行保留）。', '',
         '## 4. 问题卡（假设模板 v2 十项；全部 Q）', tpl_table(sorted(T)), '',
         '## 5. 记录 B（方式 B：事前整表授权；`registration/record_B_preauthorized_E6j.json`）',
         '- 授权对象 = 本包冻结清单内全部 B 描述符 × 两后段 + 其 COMMON_SUPPORT / 控制 / 随机派生闭包。',
         '- 生效条件：① Stage 0 六项锚全 PASS；② `routing_review_A1_auto.md` 七项全 PASS；③ 进入 Stage 3 时 `B_package_manifest.json` sha 与本授权时相同（任何 amendment 使授权失效）。',
         '- 不设"两推导段中位 ≤ 0 不进"的门；不在冻结清单内的对象不算后段账户。',
         '- 锁定值同 P 包：' + lock_txt]
    J.atomic_write_text(os.path.join(OUT, 'preregistration_B.md'), '\n'.join(b) + '\n')
    rb = dict(approval_id='E6J-RECORD-B-PREAUTH-20260926', mode='B：事前整表授权（Stage A 两包冻结时）',
              user_quote='B', user_quote_date='2026-09-26', source_file='E6j_RULING_20260926.md',
              source_sha256=J.sha_file(os.path.join(J.RES, 'E6j_RULING_copy.md')),
              frozen_manifest='registration/B_package_manifest.json', frozen_manifest_sha256=B_manifest_sha,
              objects=dict(descriptors='registry/descriptors_B.csv', n_per_segment=a0['counts']['B_per_segment'], cs='registry/cs_B.csv',
                           controls='registry/controls.csv', post_segments=list(J.POST_SEGS)),
              closure='全部 B 描述符 × 两后段；每个描述符的 COMMON_SUPPORT 子 / 父、同资本、随机三类路径与分表控制',
              conditions=['Stage 0 六项锚全 PASS（source_manifest.json stage0_all_pass）', 'routing_review_A1_auto.md 七项全 PASS',
                          '进入 Stage 3 时 B_package_manifest.json sha 与 frozen_manifest_sha256 相同'],
              status='pending_conditions', written_at=now)
    J.atomic_write_json(os.path.join(OUT, 'record_B_preauthorized_E6j.json'), rb)
    outs = [os.path.join(OUT, f) for f in ('preregistration_P.md', 'preregistration_B.md', 'P_package_manifest.json', 'B_package_manifest.json',
                                          'selection_exposure_ledger.csv', 'record_B_preauthorized_E6j.json')]
    J.write_receipt('stage_A_registration', outs, 'SUCCEEDED', B_manifest_sha256=B_manifest_sha)
    print('registered', now, 'B manifest', B_manifest_sha[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())
