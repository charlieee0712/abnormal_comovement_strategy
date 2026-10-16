# -*- coding: utf-8 -*-
"""E6m N8（B3 先行）+ N9（X01 诊断）补充交付：README_N8.md、代码变更登记（N8 / N9 段）、经验条目 N10–N16、补充交付清单 sha；
--copy 时复制到 handoff/E6m/stageN_supp_N8_<时间>/ 并写 SHA256 清单（只复制授权 / 合同 / 测试 / 状态与计数 / 封存 / 诊断，不复制任何数值表）。
只读状态列、计数列与文件 sha；不读任何收益或标签数值。"""
import os
import sys
import json
import time
import shutil
import argparse

import pandas as pd

import e6m_core as M

B = lambda *p: M.P('stageN', 'B3_prelim', *p)
HANDOFF = os.path.join(M.RUNS, 'handoff', 'E6m')
SINCE = '2026-10-05 07:16'
UNTIL = '2026-10-05 08:30'                          # 之后是阶段 S 开发（B2），另见 e6m_s_code_register.py
REASONS = {
    'f879337f217d18d0': ('首次部署', '—'),
    '8db0cd83db5d34dd': ('首次部署', '—'),
    '7d6ee6d4b134c9ed': ('置换供体排序改稳定排序（mergesort；同键按 ticker 序）', 'kernel tests a1 前；未产生任何 B3 输出'),
    '501ee93f66ecdc6c': ('首次部署', '—'),
    '172b6071bf7d8d6f': ('首次部署（N9 诊断件；只重定向 roles.csv 一次读取）', '—'),
    'd01d6e10c180da2d': ('首次部署（N9 诊断件）', '—'),
    'c6547a253f27b39a': ('DP 改两行滚动 + 回溯表由调用方预分配复用（同比较顺序、同平局规则）', 'kernel tests v2 8 / 8 PASS 后才用于任何 B3 输出'),
    '1da580b864135edf': ('首次部署', '—'),
    'ac9a2b79ec003af1': ('试跑（--max-days）输出改写 out_pilot/，不进正式 out/', '试跑 3 个任务'),
    '589495113095e496': ('格统计回执参数撞名（extra 里的 status）→ 改名 cell_status', 'cells a1 16 个日志移 attempts/N8_cells_a1；rerun 16 / 16'),
    '906eecde98c4d45e': ('CLEAN 对比拆 DMUP / DMDN / MISC / POSHL / POSM 五组（并发均衡；同一对比的计算不变）', '对比全量队列'),
    '84e652f3a3c7cae6': ('首次部署', '—'),
    '1ae0b1dcb0b21ae3': ('随机状态改为"有路径值才算 COMPUTED"（原按"跑过"标记）', '不重跑；封存 v2 以逐行状态重建合并状态表'),
    '209c9aeb61cdfa91': ('合并状态取 contrasts_real / contrasts_random 的逐行状态；进程级状态另存 *_process 列', '封存 v2（第一次运行读到 npz 报错，无回执）'),
    '02758a8d29250680': ('逐行状态只读 .csv（前缀同名的 npz 排除）', '封存 v2 SUCCEEDED'),
    '69cea73c438ed20a': ('DiD / Q09 行配对诊断改写 DID_FROM_COMPONENTS / Q09_CROSSTAB + 有值日数（原为结构性 0；README_N8 勘误 1）', '不重跑；只影响以后的重跑'),
}
LESSONS = [
    ('D', '实现合同 §2 写"当日域内"三分，把门内 / 拒绝集当成独立参考域；plan §7.1 称其为 pool0 的"切片"、§7.2 写"用当日 pool0 三分、clean 单独重算"',
     '开算前重读 plan 原句发现；附录 1（c6869169）在任何 B3 数值计算之前登记改正', 'B3_run_contract_addendum.md §A'),
    ('A', '回执写入时 extra 字段名 status 与 write_receipt 形参撞名；16 个格统计任务输出已写、回执未写', 'extra 一律不用 status / outputs / inputs / code 等形参名；失败日志移 attempts/ 后整组重跑',
     'attempts/N8_cells_a1/；cells rerun 回执'),
    ('A', '进程级随机状态按"是否跑过"标 COMPUTED；GATE_IN 的 DiD 在 U1 / U2 真实无值日时出现"真实退化 + 随机已算"8 行', '状态一律从数据推出（有值才算 COMPUTED）；封存 v2 用逐行状态重建合并表，旧值存 *_process 列',
     'seal_B3_prelim.json（status_relabelled_from_row_level = 8）'),
    ('A', '封存按文件名前缀取逐行状态，把同前缀的 npz 当 CSV 读，报解码错误', '按前缀 + 扩展名双条件取文件', '封存 v2 第一次运行（无回执）'),
    ('A', 'traceback 带出代码目录真实路径（云机代码目录挂在另一前缀下）；本地终端的脱敏正则只盖住 /mnt/sda2/<x>/', '日志在封存前统一 M.san；终端脱敏正则改为 /sda2/<x>/ 通配', 'attempts/N8_cells_a1/（16 个）'),
    ('F', '一条 ssh 命令里 "a && b && nohup c &" 把整条链放到后台，后台子壳占住 ssh 输出通道，本地命令超时转后台', '启动后台作业单独一条 ssh，后台进程全部重定向', '对比队列启动'),
    ('C', 'roles.csv（X01）在阶段 N 被当作"账户侧硬阻断、只能等原件"；实际 e6e_core 只用 factor / worst_pooled 两列，E6 REPORT 印表与 e6f_core.py:185 注释都写明 7 因子全为 5',
     '文本重建 + 垫片诊断：账户侧 15 个模块全部 import，import 期只读重建表，HB 7 因子与文本一致；作为阶段 S 云机备选件待用户授权', 'stageN/x01_diag/'),
    ('A', 'DiD / Q09 行在配对诊断表里是结构性 0（逐日循环不写诊断），执行端据此解释门内 DiD 无值日——用空仪器当证据', '改看两个分量对比的配对计数（结论不变、依据更正）；脚本改写模式与有值日数；勘误单列不改封存件', 'README_N8_erratum_1.md'),
    ('C', '告诉用户"代码支持用环境变量把结果目录指到别处"，实际 e6k_core:28 / e6l_core:33 对 E6J_RES 重定向显式报错，e6j_core.E6I_RES 写死', '源码守卫先 grep 再下结论；对用户的表述当场更正', '本节 advisor 讨论'),
]


def readme(seal):
    st = pd.read_csv(B('b3_status_N8.csv'), dtype=str, keep_default_na=False)
    ci = pd.read_csv(B('b3_cells_index_N8.csv'), dtype=str, keep_default_na=False)
    ev = pd.read_csv(B('work', 'events_counts.csv'))
    tests = pd.read_csv(B('tests', 'b3_kernel_tests.csv'), dtype=str, keep_default_na=False)
    diag = json.load(open(M.P('stageN', 'x01_diag', 'x01_import_closure.json'), encoding='utf-8'))
    q = [l for l in open(B('logs', 'queue.log'), encoding='utf-8').read().split('\n') if l.strip()]
    stc = st.groupby(['segment', 'real_status', 'random_status']).size().reset_index(name='rows')
    L = ['# E6m N8 · B3 先行（云机）+ N9 · X01 诊断：补充说明', '',
         '用途：阶段 N 交付之后新增两件事的说明页。数字全部来自机器表（状态与计数）；B3 数值已封存，执行端未读，决策端在锚通过前也不读（brief §10）。', '',
         '## 1. N8 B3 先行', '',
         '- 授权：用户 2026-10-04 "含云机 B3 先行"（`stageN/B3_prelim_authorization.json`，sha256 %s）。' % M.sha_file(M.P('stageN', 'B3_prelim_authorization.json'))[:16],
         '- 实现合同：`B3_run_contract.md`（%s）+ 附录 1 `B3_run_contract_addendum.md`（%s；分类参考域改正 + 12 项细节，开算前登记）。'
         % (seal['contract']['main'][:16], seal['contract']['addendum_1'][:16]),
         '- 冻结清单不变：660 格、65 个对比 × U0 / U1 / U2 × 两种随机 = 390 行；四段、四域（POOL0 主 / CLEAN 镜像 / A4b_CVRv5 门内 / 拒绝集）。',
         '- 标签：FWD_SOURCE（源函数逐字）/ FWD_ENDPOINT / FWD_LINEAR × h {1, 3, 5, 10, 20}；自身基准 + pool0 桥。随机各 1,024 路径（P5 块）。',
         '- 全部结果标 `HISTORICAL_CONDITIONAL_RESULT_EXPOSED`、坐标 `ANCHOR_PENDING`（kQ、状态为云机源函数重算）。', '',
         '### 1.1 事件表（形成日 × 域成员）', '', '| 段 | 域 | 形成日 | 事件 |', '|---|---|---:|---:|']
    for r in ev.itertuples():
        L.append('| %s | %s | %d | %d |' % (r.segment, r.domain, r.days, r.events))
    L += ['', '门内 + 拒绝 = pool0（四段逐段相等）；门内名单与 N5 pool2 部件逐格一致（0 差）。', '',
          '### 1.2 覆盖与状态（封存 `seal_B3_prelim.json`，sha256 %s）' % M.sha_file(B('seal_B3_prelim.json'))[:16], '',
          '- 格：%s' % '；'.join('%s %d / 660（空格 %d）' % (c['segment'], c['summary_cells'], c['empty']) for c in seal['cell_coverage']),
          '- 对比状态行：%s' % '；'.join('%s %d / 390' % (c['segment'], c['status_rows']) for c in seal['contrast_coverage']),
          '- 队列 %d 个任务全部 rc = 0；封存文件 %d 个（含 sha）。' % (seal['queue']['jobs_done'], len(seal['files'])), '',
          '| 段 | 真实 | 随机 | 行 |', '|---|---|---|---:|']
    for r in stc.itertuples():
        L.append('| %s | %s | %s | %d |' % (r.segment, r.real_status, r.random_status, r.rows))
    L += ['', 'DEGENERATE_CONDITIONAL_CONTROL：登记的 Q11 U1 / U2（同业状态在行业层内恒定，每段 16 行）；另有门内 DiD 的 U1 / U2 在部分段真实无值日'
          '（门内 QUIET × 位置格小，层内两侧难同时出现）。其中 2 行随机路径有值而真实无值，如实保留。NOT_APPLICABLE：U0 非配对的 R_PAIR_SWAP、CLEAN 的 U2、CLEAN 的 Q09。', '',
          '### 1.3 内核对拍（合成数据）', '', '| 测试 | 状态 | 用例 |', '|---|---|---:|']
    for r in tests.itertuples():
        L.append('| %s | %s | %s |' % (r.test, r.status, r.cases))
    L += ['', '### 1.4 锚通过后的处理（合同 §7）', '',
          '47 恢复或 X01 + P3 到云机后：Stage 0 A2 锚（Q 缓存、状态缓存）通过 → 原样并入结果目录，标 `COMPUTED_BEFORE_ANCHOR, ANCHOR_PASSED`；不通过 → 全部作废重算，旧产物留档标 `ANCHOR_FAILED`。', '',
          '## 2. N9 X01 诊断（不产生研究结果）', '',
          '- E6 REPORT §(B) 印出的 roles 表（本地 `exec_briefs/E6_REPORT.md` 第 109–145 行）→ `registry/x01_roles_text_reconstructed.csv`（35 行；e6e_core 只用 factor / worst_pooled）。',
          '- 垫片 `e6m_x01_shim.py` 只重定向这一次读取（不改源模块、不写 results/）：账户侧模块 import %s；import 期打开的数据文件只有重建表。'
          % '、'.join('%s %s' % (m['module'], m['status']) for m in diag['modules']),
          '- HB 7 因子与文本一致：%s。' % ('是' if diag['hb_all_match'] else '否'),
          '- 用途：阶段 S 云机备选（brief A6 之外的路径），**未经用户授权不用于任何账户计算**。', '',
          '## 3. 代码与经验', '', '- 代码变更登记：`stageN/code_change_register_N8.md`；经验条目：`stageN/lessons_N8.md`（N10–N16）。', '']
    return '\n'.join(L) + '\n'


def code_register():
    D = pd.read_csv(M.P('code_register', 'deploy_log.csv'), dtype=str, keep_default_na=False)
    D = D[(D.time >= SINCE) & (D.time < UNTIL)]
    L = ['# E6m N8 / N9 代码变更登记（续阶段 N 登记；附录 D-3）', '', '版本存档：`code_register/versions/<文件>.<sha16>`。', '',
         '| 时间 | 文件 | 动作 | sha256（前 16） | 上一版 | 触发 / 范围 | 影响面 |', '|---|---|---|---|---|---|---|']
    ok = True
    for r in D.itertuples():
        why, eff = REASONS.get(r.sha256[:16], ('首次部署', '—') if r.action == 'NEW' else ('（未登记原因）', ''))
        ok &= why != '（未登记原因）'
        ok &= os.path.exists(M.P('code_register', 'versions', '%s.%s' % (r.file, r.sha256[:16])))
        L.append('| %s | %s | %s | %s | %s | %s | %s |' % (r.time, r.file, r.action, r.sha256[:16], r.prev_sha256[:16] or '—', why, eff))
    L += ['', '每条部署都有原因与存档：%s。' % ('是' if ok else '否')]
    return '\n'.join(L) + '\n', ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--copy', action='store_true')
    a = ap.parse_args()
    seal = json.load(open(B('seal_B3_prelim.json'), encoding='utf-8'))
    if not seal['all_ok']:
        raise RuntimeError('封存未通过')
    M.atomic_write_text(B('README_N8.md'), readme(seal))
    reg, ok = code_register()
    M.atomic_write_text(M.P('stageN', 'code_change_register_N8.md'), reg)
    les = ['# E6m N8 / N9 经验条目（续阶段 N N1–N9；六类 A 仪器 / B 未匹配比较 / C 机制未读源码 / D 前提外推 / E 过早收口 / F 节奏文档）', '',
           '| # | 类 | 事件 | 做法 / 改法 | 证据 |', '|---|---|---|---|---|']
    for i, (c, e, f, ev) in enumerate(LESSONS, 10):
        les.append('| N%d | %s | %s | %s | %s |' % (i, c, e, f, ev))
    M.atomic_write_text(M.P('stageN', 'lessons_N8.md'), '\n'.join(les) + '\n')
    files = [M.P('stageN', 'B3_prelim_authorization.json'), B('B3_run_contract.md'), B('B3_run_contract_addendum.md'), B('README_N8.md'),
             B('seal_B3_prelim.json'), B('b3_status_N8.csv'), B('b3_cells_index_N8.csv'), B('tests', 'b3_kernel_tests.csv'), B('work', 'events_counts.csv'),
             B('b3_queue.sh'), B('b3_jobs.txt'), M.P('stageN', 'code_change_register_N8.md'), M.P('stageN', 'lessons_N8.md'),
             M.P('stageN', 'x01_diag', 'x01_import_closure.csv'), M.P('stageN', 'x01_diag', 'x01_import_closure.json'),
             M.P('stageN', 'x01_diag', 'x01_import_opens.csv'), M.P('registry', 'x01_roles_text_reconstructed.csv'),
             M.P('registry', 'x01_roles_text_reconstructed.provenance.json'), M.P('registry', 'E6_REPORT_roles_excerpt.md'),
             B('README_N8_erratum_1.md'), M.P('stageN', 'STAGE_S_IMPL_PLAN.md'), M.P('stageN', 'code_change_register_stageS_dev.md')]
    man = pd.DataFrame([dict(path=M.rel(p), bytes=os.path.getsize(p), sha256=M.sha_file(p)) for p in files])
    M.atomic_write_csv(M.P('stageN', 'supp_N8_manifest.csv'), man)
    outs = [B('README_N8.md'), M.P('stageN', 'code_change_register_N8.md'), M.P('stageN', 'lessons_N8.md'), M.P('stageN', 'supp_N8_manifest.csv')]
    dst = ''
    if a.copy:
        dst = os.path.join(HANDOFF, 'stageN_supp_N8_%s' % time.strftime('%Y%m%d_%H%M'))
        os.makedirs(dst, exist_ok=False)
        lines = []
        for p in files + [M.P('stageN', 'supp_N8_manifest.csv')]:
            q = os.path.join(dst, M.rel(p))
            os.makedirs(os.path.dirname(q), exist_ok=True)
            shutil.copy2(p, q)
            lines.append('%s  %s' % (M.sha_file(q), M.rel(p)))
        M.atomic_write_text(os.path.join(dst, 'HANDOFF_SHA256.txt'), '\n'.join(lines) + '\n')
        bad = [l for l in lines if M.sha_file(os.path.join(dst, l.split('  ', 1)[1])) != l.split('  ', 1)[0]]
        if bad:
            raise RuntimeError('复制后 sha 不符：%s' % bad)
    M.write_receipt(os.environ.get('E6M_TASK', 'N8_supp_deliver'), outs, status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__],
                    handoff_dir=M.san(dst), files=len(files))
    print(json.dumps(dict(register_ok=ok, files=len(files), handoff=M.san(dst)), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
