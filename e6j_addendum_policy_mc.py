# -*- coding: utf-8 -*-
"""一次性写入：P 政策 / MC 执行口径追记（P 包封存与政策读数之前）。只新增文件，不改已登记文件
（source_resolution.md 的 sha256 已记入 source_manifest.json，故追记另起 source_resolution_addendum_policy_mc.md）。"""
import e6j_boot  # noqa: F401
import os
import glob
import time

import e6j_core as J

now = time.strftime('%Y-%m-%d %H:%M:%S')
rr = sorted(glob.glob(os.path.join(J.RES, 'task_status', 'run_prand_*.receipt.json')), key=os.path.getmtime)
state = dict(seal_P_exists=os.path.exists(os.path.join(J.RES, 'registration', 'seal_P.json')),
             policy_final_exists=os.path.exists(os.path.join(J.RES, 'results_P', 'pilot_policy.csv')))
assert not any(state.values()), state
state.update(randoms_P_exists=os.path.exists(os.path.join(J.RES, 'randoms', 'P')), run_prand_receipts=len(rr),
             first_run_prand_receipt_mtime=(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(rr[0]))) if rr else None))
dry = {os.path.relpath(p, J.RES): dict(sha256=J.sha_file(p), mtime=time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(p))))
       for p in sorted(glob.glob(os.path.join(J.RES, 'results_P', 'dryrun', '*.csv')))}
rules = {
    'written_at': now,
    'state_at_write': state,
    'scope': 'P 包政策评分（plan §4.5）与 MC 增补（plan §8.1 / brief W14）的执行口径；plan 未给数值的地方由执行端在读数前声明',
    'code_sha256': {f: J.sha_file(os.path.join(J.CODE, f)) for f in ('e6j_policy_p.py', 'e6j_seal.py', 'e6j_mc_topup.py', 'e6j_test_policy_seal.py')},
    'rules': [
        'MC-1 主比较 = e-随机：R-MATCH-SRC（IID）两后段 × 六形态 × 四主臂（S / M / SM / C1）× 12 个 (α, H) 格；MCSE = sd(配对路径差) / √n（真实账户固定 → 随机路径年化 net8 的 sd / √n）',
        'MC-2 某 (后段, 形态, 臂) 的 12 格最大 MCSE > .03 → 以 512 路径为单位增补，块数按当前 sd 估计的需要路径数一次排队（ceil(n·(MCSE/.03)^2)），新 path_index 接在已用最大路径号之后、不挑 seed；每轮增补后先追加封存版本再重算',
        'MC-3 8,192 为首个资源复核点：到点仍 > .03 → 列表交用户，不静默停止、不静默放宽',
        'MC-4 增补决定只用 MCSE（随机路径离散度），不读真实账户、不算真实 − 随机；读政策结果后本轮不再增补（MC 未定项只标 MC_UNRESOLVED / 待精化）',
        'MC-5 "MC 误差仍影响符号" := |真实 − 随机均值| < 2·MCSE（不论 MCSE 是否 ≤ .03）→ 该段 e-随机未定；任一后段非正已定 → e-随机 FAIL；两段正已定 → PASS',
        'V-1 判定：已定的 FAIL 优先且全部列出（不通过（c、e随机 …））；无 FAIL 而有未定项 → 不可判（项:状态）；否则通过。MC_UNRESOLVED 不再是无条件前置门',
        'V-2 e-资本：原生与同资本在同一 profile 下比较符号，0 的数值舍入容差 1e−9 年化百分点（不设收益死区）；同资本缺 → NA → 不可判',
        'V-3 市值通道：逐段 abs(mean_t gap_t) ≤ 5 百分位点；无"两边都有编辑"的段为 N/A（不当 0、不进闸，size_na_segments 列出）；四段全 N/A → N/A',
        'V-4 POLICY_INTERPRETATION_PENDING = 主臂上 FULL 与 G4 的结论类（通过 / 不通过 / 不可判）不同；主解释仍为 FULL（W07），G4 并印',
        'V-5 c 项 NA 不自动满足（plan §4.5 c）',
        'B-1 研究块 B：逐描述符报 MCSE 与 MC 状态（同 MC-5）；主比较 = 主配置 α .25 × H5 的 IID 参照，其 MCSE > .03 时按 MC-2 对该 (段, 母体, 块) 增补；推导段测时分片估计的路径离散度 sd 中位 ≈ .09、最大 ≈ .33（1,024 路径 MCSE ≈ .003–.010），预计不触发',
    ],
    'self_test': 'e6j_test_policy_seal.py：合成临时目录 16 / 16 PASS（e-随机九例、0 容差、判定八例、封存 v1 / v2 / v3 追加与改动拒绝、增补计划与路径区间、S / SM 分片精确匹配）',
    'disclosed_deviation': 'P 原生账户曾于封存前被 e6j_policy_p.py --dryrun 读取一次以跑通代码路径（输出 results_P/dryrun，当时无随机分片、e-随机全部缺失）；本追记的规则针对代码逻辑缺陷（MC 前置门使全部对象因缺随机而不可判、市值 NaN 被当失败、FULL / G4 差异未标），不依据任何读数；该偏差另记 lessons_delta',
    'dryrun_files': dry,
    'timeline_check': 'dryrun 文件 mtime → 本追记 written_at → registration/seal_P.json sealed_at → results_P/pilot_policy.csv 回执时间，四者应依次递增',
}
p = os.path.join(J.RES, 'registration', 'policy_P_operational_addendum.json')
assert not os.path.exists(p)
J.atomic_write_json(p, rules)
md = ['# E6j source_resolution 追记：P 政策 / MC 执行口径（%s，P 包封存与政策读数之前）' % now, '',
      '用途：plan §4.5 / §8.1 未给数值处的执行端声明。`source_resolution.md` 的 sha256 已记入 `source_manifest.json`，故不改原文件、另起本文件。'
      '机器可读版 `registration/policy_P_operational_addendum.json`（sha256 %s）。' % J.sha_file(p)[:16], '']
md += ['- ' + r for r in rules['rules']]
md += ['', '- 披露：' + rules['disclosed_deviation'], '', '| dryrun 文件 | sha256 前 16 | mtime |', '|---|---|---|']
md += ['| `%s` | %s | %s |' % (k, v['sha256'][:16], v['mtime']) for k, v in dry.items()]
md += ['', '写入时状态：%s' % state, '']
pm = os.path.join(J.RES, 'source_resolution_addendum_policy_mc.md')
assert not os.path.exists(pm)
J.atomic_write_text(pm, '\n'.join(md))
J.write_receipt('policy_P_operational_addendum', [p, pm], 'SUCCEEDED')
print('addendum', J.sha_file(p)[:16], J.sha_file(pm)[:16], now, state)
