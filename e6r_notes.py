# -*- coding: utf-8 -*-
"""E6r REVIEW 注记与代码变更登记（brief §8 / §9；用户 10-11 定：跑批途中的待决事项不中途发消息，写进交付报告专节 §8）：
reports/E6r_REVIEW_input_notes.md、reports/E6r_code_change_register.md。数字从机器表与回执取；不写登录信息、主机标识或用户目录。
用法：python3 e6r_notes.py [--root <相对 E6R_WORK 的根>]"""
import os
import re
import glob
import json
import argparse

import numpy as np
import pandas as pd

import e6r_core as O

PENDING = [
    ('CVR5 缺失口径', '源 features_daily.py A3 的 CVR_5d = rolling(5, min_periods=3)（CVR_20d 为 rolling(20, min_periods=10)）；brief §0.1 #13 写"缺失规则逐字不变"，'
                      '本轮照源（5 日窗 3 个有效即出值），未改成 5 / 5。e6r_cache 段内重算与 E6i 物化值逐格 0 差。请决策端确认此读法。'),
    ('entry_tertiles 的 G4 行', '计数与资本份额是可加会计量，逐列四段中位后恒等不成立（S0 首跑 1 处 DIFFERS 即此）→ G4 行 NOT_APPLICABLE、数值留空；S0 重跑 0 DIFFERS；首跑件保留在 tmp/s0_run1/。'),
    ('入场 TICKETS / JOINT 求解器与节点上限', '沿用 E6q rt_match（票据降序 × 固定稳定优先序的首个可行映射；四条必要条件剪枝 + 同额对称性）。节点上限 20 万 → 2 万：76 条真实路径、'
                                          '290,548 次抽样（20 万上限）中，可行实例需 2–20 万节点的只 71 次（0.024%），触限实例占全部节点 78%；改 2 万后单路径 53 → 11 s。'
                                          '触限当日该路径保留同快照 would-be 真实票据（原映射见证），计入 random_tilt_feasibility.n_algorithm_limit。'
                                          '另试过 v2（字典序贪心 + 原映射见证 + 2-交换 / BFD 证书 + 精确回溯）：38.9 万实例与 v1 比对，v1 可解实例上 v2 无一给出不同解，'
                                          '但 v2 对不可行位置的证明更弱、触限多约 5 倍 → 未采用（代码留在引擎 rt_match2，RT_VER = 0 不调用）。'),
    ('额外批次的抽样状态', 'DY 的 er_status 只记常规批次；新增 er_c_feas / er_c_nom / er_c_lim / er_c_id / er_c_deg 五列按日计数（常规 + 额外批次），可行性表用计数列。'),
    ('随机路径 A2 → B 续跑', 'A2 末存紧凑 checkpoint（引擎原函数 compact_lots 后存；意向表只存在册批次引用的行；不存 DY；压缩），B 相续跑；推导段字段取同一路径 A2 读数'
                           '（确定性同值）。开发期续跑 vs 整段 48 / 48 逐位同（含紧凑版）；B 相每个 (owner, 机制) 的 0 号路径整段重跑并与续跑逐位比对'
                           '（identities CHECKPOINT_RESTORE_IDEMPOTENT）。checkpoints/A2_rand/ 为可删临时件（列入清理候选，本轮不自删）。'),
    ('成交日志标签列', '引擎只在有标签的成交行写 cohort / 标签 / T0 状态列，成交日志缓冲区分块落盘后复用 → 无标签行（部分额外批次 / 部署买入）会带上一块的残留值。'
                       'A1 后、任何后段运行前修正（e6r_acct / e6r_run：分配时与每次落盘后重置为哨兵，导出为空；引擎未改）；账户 A2 以同一引擎重跑只为重生成成交分片'
                       '（账户结果逐位不变），旧分片保留在 tmp/stale_tl_labels_*/。'),
    ('size_dev_pp 符号', '正 = 偏小盘（同退出 FLAT 参照的 clean 市值分位资本加权均值 − 本账户，× 100），按附录 E CC-E6r-03 的建议约定；port3t 两列为本账户 − 参照（政策只用 |·|）。'),
    ('随机控制可比性阈值（执行端代拟）', '沿 E6q：AMOUNT_MATCH_V2 / ISK 类 FULL unmatched / requested > .25、BERNOULLI 强度比不在 [.8, 1.25]、TICKETS / JOINT 触限 + 无解份额 > .25 '
                                     '→ CONTROL_NOT_COMPARABLE（plan 未给数）；入场随机无一次非恒等抽样 → STRUCTURAL_DEGENERATE。两者各段同标，c4 记 NA 并写原因。'),
    ('局部快照两类不另跑', 'RAW_TILT_WITHIN_CELL_TICKETS（122）与 GATE_TILT 两种部分随机（12）：brief 写局部快照只读、不跑 → NOT_APPLICABLE + 缺因；'
                           '两层预算 / 费用桥（225）按 owner 逐段计算（不含费口径）。'),
    ('GW08 不可算', '混合 Q 真实分数与记忆年龄不在缓存（A4b 合成只存形成权重）→ NOT_COMPUTABLE；能算的代理（权重离散度、名单变动率）并报。'),
    ('磁盘', '用户 10-24 提议清理 47 临时文件：查明快满的是系统根分区（含 /tmp），由其他用户 / 服务占用，本轮在根分区上约 0；结果盘 44T 余约 36T。未删任何文件'
             '（brief R9）。可删候选（待用户点名）：E6p tmp 102G、trades_parts 122G；E6q tmp 34G、trades_parts 18G；本轮 checkpoints/A2_rand。'),
    ('并发与 NUMA（用户 10-24 授权：47 空闲时可适当多于 96）', 'B 相随机在 21,000 / 45,598 批落盘点（47 时间 23:25）由 96 → 176 workers（CPU 0-79,96-191，每物理核一个；'
                                                       '留 16 个物理核与全部超线程），首个 3,000 批 1,846 s，反比 96 时慢。诊断：47 的 3.10 内核开着 NUMA 自动均衡，'
                                                       '跨两路的 fork 池共享页被反复迁移（约 1.1 万页 / s，提示缺页约 44 万 / s），worker 约 31% 时间卡在页锁。'
                                                       '改法：e6r_membind.py 包装（MPOL_BIND{0,1}，不带 MOF 标志 → 内核不对这些进程做均衡迁移；分配仍本地优先），'
                                                       '在下一落盘点以链 B3 续跑；单进程对照：默认策略 30 s 内约 72 万次提示缺页，包装后 0。只影响内存放置，'
                                                       '随机种子与计算不变，结果逐位相同（续跑跳过已完成批次，0 号路径整段比对照常）。'
                                                       '包装后核利用率 68–77% → 98–99%、页迁移 1.1 万 → 15 / s，但 B3 首个 3,000 批 1,450 s（≈ 2.07 批 / s）仍只略好于 96：'
                                                       '按路分组的读字节速率显示 node0 worker 进度约为 node1 的 1 / 3.6（两路同频 2.4 GHz）——父进程在 node1 上建的'
                                                       '形成层数组（约 2.6 GB）与市场缓存页（约 1.2 GB）被 node0 worker 跨路读。再改：e6r_run.py 加多池派发（E6R_POOLS；'
                                                       '第一池沿用父进程状态在 node1，第二池先把父进程绑到 node0、从市场缓存六个子目录的逐字节副本 tmp/cache_node0'
                                                       '（129 个文件 sha256 全同）重建市场与形成层再 fork；哪个池先空就派给哪个池），单池 vs 多池同一组批次逐行比对见 '
                                                       'tmp/diag（不进交付）。单进程探针：每批冷 / 热缓存差 ≤ 5%（加载开销小，不做分块）。'
                                                       '多池（B4，随机末 3,598 批 + 增补第 1 轮前段）仍未提速：两路同时跑同一微基准，node0 空闲核纯 Python 计算只有 node1'
                                                       '（主核忙的超线程）的约 1 / 6.5、随机访存相当；增补第 1 轮前 3,000 批按池计数：node1 96 workers 完成 2,500 批、'
                                                       'node0 80 workers 500 批（每 worker 26.0 vs 6.2，同一任务流动态派发）——socket 0 核心在硬件 / 固件层被限频（两路 cpufreq 设置相同：'
                                                       'conservative 1.5–2.4 GHz、boost 开；非 OS 设置，未改）。增补第 1 轮 3,000 批起试只用 node1 全部逻辑核'
                                                       '（96 物理 + 96 超线程 = 192 workers，链 B5）：下一个 3,000 批 5,630 s（0.53 批 / s），比双池（0.92）慢 42%、比 node1 96 物理核'
                                                       '单独贡献（0.765）慢 30%，两段机制构成相同（退出层 96–98%）、匿名页全在 node1 → 超线程在此负载上是负作用。'
                                                       '故自第 1 轮 6,000 批起回到双池并加慢路收尾（链 B6：node0 池不排队、未派发 < 800 批后停派，避免每轮末尾等慢路），'
                                                       '统计到闭包门只用 node1 物理核（链 B7，CPU 96-191）。建议下一轮：只用 node1 物理核或双池 + 收尾规则、不开超线程，并请管理员查 socket 0 限频。'),
]


def table(rows, heads):
    out = ['| ' + ' | '.join(heads) + ' |', '|' + '---|' * len(heads)]
    for r in rows:
        out.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    return out


def jl(p):
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='')
    a = ap.parse_args()
    root = O.P(*a.root.split('/')) if a.root else O.work()
    W = O.work()
    rd = lambda rel: pd.read_csv(os.path.join(root, rel), dtype=str, keep_default_na=False) if os.path.exists(os.path.join(root, rel)) else pd.DataFrame()
    ID = rd('verify/identities_E6r.csv')
    REP = rd('verify/replication_E6r.csv')
    RD = rd('statistics/randoms_E6r.csv')
    CLS = rd('verify/closure_E6r.csv')
    st = jl(os.path.join(root, 'statistics', 'stats_facts_E6r.json'))
    g1 = jl(O.P('diagnostics', 'g1_facts_E6r.json'))
    fz = jl(O.P('registration', 'freeze_E6r.json'))
    fr = RD[RD.segment == 'FULL'] if len(RD) else RD
    lines = ['# E6r REVIEW 输入注记（执行端；协议 v1.6、方式 B）', '',
             '> 页首：E7 不做（e7 = HOLD）；deployment_authorized = false；授权九值见 R0；连续全历史（CASH_V0）为主读。', '',
             '## §1 交付范围', '',
             '- 账户 350（FEASIBLE 341 + IDEAL 9）；比较 2,988；复合 20；随机引用 1,408（随机 1,314 + 确定性 94）；成本反馈 202 / 1,822；快照 359；E 7 / Q 18 / CC 9 / G 12。',
             '- 支持日 %s；闭包门 %s。' % (st.get('support_days', '—'), ('%d / %d PASS' % ((CLS.status == 'PASS').sum(), len(CLS))) if len(CLS) else '—'), '',
             '## §2 源绑定与复现', '',
             '- 58 个 E6q 同坐标锚（FLAT）× 四段逐日 DY 前 102 列：%s。' % (('%d / %d PASS' % ((REP.status == 'PASS').sum(), len(REP))) if len(REP) else '—'),
             '- 恒等 %d 项：%s。' % (len(ID), '、'.join('%s %d' % kv for kv in ID.status.value_counts().items()) if len(ID) else '—'),
             '- A1 冻结：%s（SCHEMA 合同 sha16 %s）。' % (fz.get('written_at', '—'), str(fz.get('schema_contract_sha256', ''))[:16]), '',
             '## §3 段口径', '', '连续全历史（CASH_V0）：A2 推导段末 checkpoint → B 续跑，跨段不重置；FULL = 段支持日加权，G4 = 四段中位。', '',
             '## §4 随机与匹配', '',
             '- FULL 状态：%s；路径数中位 %s。' % ('、'.join('%s %d' % kv for kv in fr.status.value_counts().items()) if len(fr) else '—',
                                                ('%.0f' % np.nanmedian(pd.to_numeric(fr.paths, errors='coerce'))) if len(fr) else '—'),
             '- MC_LIMIT 引用（达 1,024 路径 FULL MCSE 仍 > .01）：%d 条（明细见 E6r_limit_register.md 与 statistics/randoms_E6r.csv）。' % (int((fr.status == 'MC_LIMIT').sum()) if len(fr) else 0), '',
             '## §5 成本', '', '- canonical curve 仪器（κA^δ S_δ，固定路径）；4 个 E6q 曲线锚在 E6r 仪器上复现（verify/curve_replication_E6r.csv）；反馈 202 路径冲击实扣现金。', '',
             '## §6 政策', '', '- 两映射：E6R_POLICY_ESTIMAND（主；ENTRY_OVERLAY → 同退出 FLAT、EXIT_RULE → 无退出父）与 E6Q_ORIGINAL_AUDIT（审计；无退出父）；verdict 由 8 字段显式 bool 重算。', '',
             '## §7 诊断', '', '- D1–D12、landmark、T0 → age1 转移（四分母）、359 快照、两层投影、门反事实；第一道 G1：%s。' % (
                 '、'.join('%s %s' % kv for kv in sorted(g1.get('labels', {}).items())) or '—'), '',
             '## §8 待决事项（执行端代拟；用户 10-11 定：不中途发消息）', '']
    for i, (k, v) in enumerate(PENDING, start=1):
        lines += ['%d. **%s**：%s' % (i, k, v)]
    # 资源实耗：链日志
    cl = O.P('logs', 'chain.log')
    steps = []
    if os.path.exists(cl):
        st_ = {}
        for l in open(cl, encoding='utf-8', errors='replace'):
            m = re.match(r'\[(.+?)\] (start|done|FAILED) (\S+) (\d+) (\S+)', l)
            if m:
                ts = pd.Timestamp(m.group(1))
                key = (m.group(3), m.group(4), m.group(5))
                if m.group(2) == 'start':
                    st_[key] = ts
                elif key in st_:
                    steps.append(['%s #%s %s' % key, '%.0f' % (ts - st_[key]).total_seconds(), m.group(2)])
    lines += ['', '## 资源实耗（链日志步骤耗时，秒）', ''] + (table(steps, ['步骤', '秒', '状态']) if steps else ['—']) + ['']
    O.atomic_write_text(os.path.join(root, 'reports', 'E6r_REVIEW_input_notes.md'), '\n'.join(lines) + '\n')
    # 代码变更登记
    here = os.path.dirname(os.path.abspath(__file__))
    a1 = fz.get('code_sha256', {})
    rows = []
    for f in sorted(os.listdir(here)):
        if f.startswith('e6r_') and f.endswith(('.py', '.sh')):
            sha = O.sha_file(os.path.join(here, f))
            rows.append([f, sha[:16], a1.get(f, '')[:16] or '（A1 后新增）', 'no' if a1.get(f) == sha else 'yes'])
    cc = ['# E6r 代码变更登记（A1 冻结后；经济规则未变）', '',
          '| 位置 | 变更 | 原因 | 影响 |', '|---|---|---|---|',
          '| e6r_acct.py / e6r_run.py | 成交日志标签列在分配时与每次落盘后重置为哨兵 | 缓冲区复用导致无标签行带残留标签 | 只影响成交导出的标签列；账户结果逐位不变；A2 成交分片以同一引擎重生成，旧分片保留 |',
          '| e6r_acct.py / e6r_run.py / e6r_core.py | 随机路径 A2 末紧凑 checkpoint（compact_lots + 稀疏意向行 + 不存 DY + 压缩）与 B 续跑合并 A2 推导段字段；0 号路径整段重跑比对 | 存档体积 4.7 → 0.17 MB / 路径 | 结果与整段一次跑完逐位相同（核验见 identities） |',
          '| e6r_stats / policy / g1 / diag / claims / reports / notes / closure / syncpack / dryrun | A2 启动后新增的下游模块 | 只读账户产物 | 不改任何账户 |',
          '| e6r_chain.sh / e6r_bg.sh / e6r_after_b.sh / e6r_membind.py（新增） | CPU 绑定可配（E6R_CPUS）；链可选包装前缀（E6R_PRE）；衔接脚本按链名等待；'
          '内存策略包装（MPOL_BIND） | 用户授权提并发；规避 3.10 内核 NUMA 自动均衡的跨路页迁移 | 只影响调度与内存放置；结果逐位不变 |',
          '| e6r_run.py | 多池派发（E6R_POOLS）：每路一个 fork 池，第二路从市场缓存逐字节副本重建市场与形成层；动态派发（快路在途 2n）；'
          '慢路收尾（第 4 段 tail：慢池不排队、未派发 < tail 后停派）；各池完成批数入日志；未设则单池原路径 | '
          'node0（socket 0 限频）单 worker 进度约为 node1 的 1 / 4–1 / 6 | 每批仍调用同一 job_random；单池 vs 多池逐行比对相同；结果逐位不变 |', '',
          '## 文件 sha（交付时 vs A1）', ''] + table(rows, ['file', 'sha256（16）', 'A1 时', 'changed_after_A1'])
    O.atomic_write_text(os.path.join(root, 'reports', 'E6r_code_change_register.md'), '\n'.join(cc) + '\n')
    print(json.dumps(dict(notes='E6r_REVIEW_input_notes.md', pending=len(PENDING), code_files=len(rows)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
