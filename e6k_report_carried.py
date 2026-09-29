# -*- coding: utf-8 -*-
"""E6k_REPORT_carried（plan §13.5：源资本 / N × 母体、领导词表、E04 历史补记链接、运行卫生、实施限制）。
输入：accounts/<段>/*（PARENT 目标统计与 H5 账本）、task_status/*、logs/worker_done.txt、verify/legacy_processes（E6j）、registration/code_record_*。"""
import e6k_boot  # noqa: F401
import os
import sys
import glob
import json

import numpy as np
import pandas as pd

import e6k_core as K
import e6k_report as RP

OUT = K.P('reports', 'E6k_REPORT_carried.md')


def head(subject, sub, unit='见列', dates='四段', expo='源母体（已暴露）'):
    return {'主体': subject, '算子': 'PARENT', '分母': '段内交易日', '基准': '—', '子集': sub, '单位': unit, '日期': dates, 'H': '5',
            '成本模型': '源 8bp', '支持': '源', '资本视图': '实际源 DEV', 'exposure': expo}


def main():
    rows = []
    for s in K.SEGMENTS:
        for f in sorted(glob.glob(K.P('accounts', s, '*__K0.npz'))):
            if os.path.basename(f).startswith('weights_'):              # 同一 glob 会匹配到权重文件（无 desc 键）
                continue
            z = K.npz(f)
            tg = list(map(str, z['targets']))
            desc = list(map(str, z['desc']))
            for j, tid in enumerate(tg):
                if not tid.endswith('|PARENT'):
                    continue
                mother = tid.split('|')[1]
                i = desc.index('K0|%s|a0|H5|PARENT' % mother)
                ws, nn, lv = z['t_wsum'][j], z['t_nnames'][j], z['t_lv5'][j]
                act = ws > 0
                rows.append(dict(segment=s, mother=mother, invested_target_mean=float(ws[act].mean()) if act.any() else np.nan,
                                 target_names_mean=float(nn[act].mean()) if act.any() else np.nan, active_days=int(act.sum()), days=len(ws),
                                 position_actual_mean=float(np.mean(z['d_pos'][i])), turnover_mean=float(np.mean(z['d_turn'][i])),
                                 net8_ann=float(np.nanmean(z['d_net8'][i])) * K.ANN, leader_size5_max_overweight_mean=float(np.nanmean(lv[act])) if act.any() else np.nan))
    rp = RP.Report('carried')
    rp.h(1, 'E6k REPORT carried —— 源资本 / N、领导词表、历史补记链接、运行卫生、实施限制')
    rp.p('用途：plan §13.5 carried。母体为源对象（已暴露）；领导词表口径 = size 五分组当"行业"的源 DEV 超配（未归一，只看超配；EXEC_LEADER_VS_PARENT 同式）。')
    rp.table(pd.DataFrame(rows), head('八母体（六生产形态 + R2 + A06）资本 / 名数 / 换手 / 8bp 净 / size 五分组最大超配', 'PARENT H5', expo='源母体'),
             'E6K-CAR-PARENTS')
    rp.h(2, '历史补记链接')
    rp.p('- E6j E04（`exec_briefs/E6j_VERIFY_report.md` §3 E04）：编辑层 size_gap 带符号为负 = 买小卖大；决策端 #70 已认。本轮全部取绝对值作门的量同印带符号列（E6j #70 / #74；报告生成器强制）。')
    rp.p('- E6j supplement_1（`E6j_REPORT_supplement_1.md`）S1–S5 事后口径；本轮 PORT3 / LEADER_VS_PARENT / DISCLOSE 为事前登记列（读数前），不回写 E6j。')
    ts = pd.DataFrame([json.load(open(p, encoding='utf-8')) for p in glob.glob(K.P('task_status', '*.receipt.json'))])
    cnt = ts.assign(kind=ts.task_id.str.split('_').str[:2].str.join('_')).groupby(['kind', 'status']).size().unstack(fill_value=0).reset_index()
    rp.table(cnt, head('回执计数（截至本报告生成前的全部回执）', 'task_status/*.receipt.json', unit='计数', expo='—'), 'E6K-CAR-RECEIPTS')
    wd = open(K.P('logs', 'worker_done.txt'), encoding='utf-8').read().split('\n')
    i_rel = next((i for i, l in enumerate(wd) if l.startswith('RELAUNCH_POST')), len(wd))
    pre = [l for l in wd[:i_rel] if 'rc=' in l]
    post_ = [l for l in wd[i_rel:] if 'rc=' in l]
    bad_pre = [l for l in pre if 'rc=0' not in l and ('2019-2023' in l or '2024-2026' in l)]
    bad_post = [l for l in post_ if 'rc=0' not in l]
    rp.p('- 工作者完成记录 %d 行（逐行见 `logs/worker_done.txt`）：推导段首轮与 MC 全部 rc=0；两后段首次启动 %d 行非 0（后段守卫的冻结清单文件名笔误，'
         '任务在守卫处退出、未读后段数据、无产物）；RELAUNCH_POST 之后 %d 行非 0（RP 逐级 MILP 复核失败），按回执名补跑（`e6k_queue_failed.py` / '
         '`e6k_chain_post2.sh`），封存核对要求队列每行回执 SUCCEEDED。' % (len(pre) + len(post_), len(bad_pre), len(bad_post)))
    rp.p('- 并发：node1（taskset 96-191,288-383），xargs 起步 24 → SIGUSR1 升至 64（用户 E6j 已批上限 64）；BLAS / polars / numba 单线程。')
    rp.p('- 遗留进程：E6j 所列 38 个（`E6j verify/legacy_processes.csv`）本轮不动；本轮只按 PID + 启动时间 + 命令行管理自身进程：结束过 1 个自身的 pgrep 自匹配等待循环；'
         '后段首次启动失败后停掉该次链的 4 个进程；RP 失败后停掉 07:31 链的 3 个 bash（保留其 xargs 跑完）。')
    rp.p('- 运行中代码改动（均在 47 上语法检查后原子替换；逐项见 WORKLOG 与 lessons_delta）：`e6k_core` 追加 `npz()` 整读（统计 / 诊断改用）；'
         '`e6k_core.post_gate` 冻结清单文件名修正；`e6k_ops` RP 恢复路径（只作用于主路径复核失败的日，成功日代码路径不变）；`e6k_run_det` facts 记恢复 / '
         'SOLVER_LIMIT 日数；`e6k_seal` / `e6k_stats --mc-plan` 队列逐行完整性核对；X04 后段补算入口（`e6k_stage0_ops` 后段过 post_gate、'
         '`e6k_a1_auto --masks-post`）；报告脚本（首看标签 / NOT_AUTHORIZED 判定、候选 / 边缘清单、R0 授权与后段表）；新增 `e6k_report_cards`（47 个登记 query 同 id 落表）'
         '与 `e6k_leafdiag`（Q05-c）；诊断 v2：`e6k_decay`（前瞻版独立 draw）、`e6k_hg_continuous` + `e6k_ops.hg_gate(hold_init)`（默认关，登记账户路径不变）；'
         '`e6k_report_carried` 权重文件 glob 修正。')
    rp.h(2, '实施限制')
    rp.p('见 `reports/E6k_limit_register.md`（L01 起）与 R0 §7。')
    rp.write(OUT)
    K.write_receipt('report_carried', [OUT], 'SUCCEEDED', queries=len(rp.qids))
    print('carried 写出：%d 个 query' % len(rp.qids), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
