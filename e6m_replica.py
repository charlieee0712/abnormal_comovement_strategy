# -*- coding: utf-8 -*-
"""E6m 阶段 N · N6：外部输入清单（brief A8 / 纪律 78）与副本包 P0–P3 schema / dry-run（brief A7 / plan §13.2）。只读。
external_inputs_E6m.csv：路径相对 results/（或标明根）、用途、读取步骤、sha256 或 SOURCE_WAIT、缺失影响、阶段（N / S）。
副本包：P0_REVIEW / P1_LEDGER / P2_RANDOM / P3_DATA_REF 目录结构与 manifest 格式；阶段 N dry-run = 把本阶段 P0 候选文件复制到
replica/dryrun/P0/ 并按 manifest 逐件重算 sha 验证；P3 记行情 / 缓存允许版本的 sha（不复制行情）。"""
import os
import sys
import json
import glob
import shutil
import hashlib

import pandas as pd

import e6m_core as M

RES_ROOT = '/mnt/sda2/<用户目录>/results/'
X = [
    ('X01', '20260904_1051_E6_wide_scan/roles.csv', 'e6e_core 模块级读取（因子"高值坏"方向表）', 'import 期（经 e6k_env → e6j_engine → e6f_core → e6e_core）', '账户侧全部步骤起不来', 'S'),
    ('X02', '20260923_0254_E6i_measurement_need_fit/registration/record_B_approved_E6i.json', 'e6i_core 模块级 load_approval_i()', 'import 期（不存在只记未加载）', '无', 'S'),
    ('X03', '20260923_0254_E6i_measurement_need_fit/cache/<段>/K_rar20__OBS.*、K_slope20__OBS.*、K_MA3_E6F__OBS.*（24）', 'S / M / C1 原值（e6j_slot.e6i_member_raw）',
     'Stage 0 c2–c6、账户、随机', 'S / M / C1 对象与 SOURCE 块不可算', 'S'),
    ('X04', '20260927_0038_E6j_k_two_dimension_pilot/cache/<段>/J_B1_qCC.{npy,json}', 'Q0 原值（e6j_slot.j_member_raw）；A2-5 锚', 'Stage 0 A2-5；账户', '云机重算 kQ 标 ANCHOR_PENDING', 'S'),
    ('X05', '20260927_0038_E6j_k_two_dimension_pilot/registry/trade_calendar.csv', '段日历（e6j_engine）', '段环境', '云机用行情索引与交易日历文件代替（c4_data_calendar）', 'S'),
    ('X06', '20260927_0038_E6j_k_two_dimension_pilot/anchors/mother_ledger_prod_v2.parquet', '母体日账本锚', 'Stage 0 A2-2 / A2-3', '账本锚不可核', 'S'),
    ('X07', '20260927_0038_E6j_k_two_dimension_pilot/results_P/pilot_policy.csv、results_B/part2_main_config_all_objects.csv、stage0/anchor2_rerun/e6i_parent_anchor.csv',
     'c1 身份原件；R2 / A06 母体锚', 'Stage 0 c1 / A2-3', 'R2 / A06 锚不可核', 'S'),
    ('X08', '20260927_0038_E6j_k_two_dimension_pilot/carried/leader_six_forms_capital.csv；accounts/B/<段>/<母体>__<块>.npz', '六形态资本锚；B 账户恒等', 'Stage 0 A2-3', '资本锚不可核', 'S'),
    ('X09', '20260923_0254_E6i_measurement_need_fit/accounts/<段>/merged_index.csv 及其指向文件', '母体账本对 E6i', 'Stage 0 c2', 'c2 不可核', 'S'),
    ('X10', '20260903_1214_delivery_pools_v2/*.csv（summary、pool1、六个 pool2）', 'A2-1 逐字节锚（结果目录原件）', 'Stage 0 A2-1', '云机改对仓库交付包（X23）核，结果目录原件待 47', 'S'),
    ('X11', '20260928_2325_E6k_k_binding_stage/results/full/policy_E6k.csv', 'W08 第一层锚（A2-4）', 'Stage 0 A2-4；carried', 'E6k 同构对象 1e−9 锚不可核', 'S'),
    ('X12', '20260928_2325_E6k_k_binding_stage/registry/descriptors_E6k.csv', '同构集合（暴露标签交集）', 'A0（S1 复判）', 'SECOND_EVALUATION 标签待定', 'S'),
    ('X13', '20260928_2325_E6k_k_binding_stage/registry/accessory_E6k.csv、randoms_E6k.csv、results/full/random_refs_<段>.csv（4）、source_manifest.json、engine_contract.md',
     'c1 身份原件；c5 随机复现（A2-6）', 'Stage 0 c1 / c5', '随机复现不可核', 'S'),
    ('X14', '20260928_2325_E6k_k_binding_stage/registry/mask_facts_deriv_E6k.csv、mask_facts_post_E6k.csv', 'Stage A 对照', 'Stage A', 'A2-7 不可核', 'S'),
    ('X15', '20260928_2325_E6k_k_binding_stage/registration/policy_profiles_E6k.json、_amend_1.json、_amend_2.json', '政策转录（W12 原件链）', 'Stage B', 'PX 原件逐句对待定', 'S'),
    ('X16', '20260928_2325_E6k_k_binding_stage/accounts/<段>/*.npz', 'c6 输出结构对锚', 'Stage 0 c6', 'c6 对锚不可核', 'S'),
    ('X17', '20260930_1141_E6l_time_memory_stage/results/full/policy_E6l.csv', 'W08 第二层锚（LAG1_10 / DECAY5_10）；SOURCE_NUMERIC_VERIFICATION_PENDING', 'Stage 0 A2-4', 'E6l 同构对象锚不可核', 'S'),
    ('X18', '20260930_1141_E6l_time_memory_stage/registry/（descriptors_E6l、mask_facts_*）', 'A2-7 HG / LAG 掩码事实；暴露交集', 'Stage A / A0（S1）', 'A2-7 不可核', 'S'),
    ('X19', '20260930_1141_E6l_time_memory_stage/registration/policy_profiles_E6l.json', 'W12 政策合同原件', 'Stage B', '按 brief 文本转录（policy_profiles_E6m_stageN.json）', 'S'),
    ('X20', '20260930_1141_E6l_time_memory_stage/results/full/random_refs_<段>.csv', 'A2-6 LAG1_10 随机复现', 'Stage 0 c5', '不可核', 'S'),
    ('X21', '20260930_1141_E6l_time_memory_stage/cache/state/state_full_E6l.npz', 'A4-3 状态序列逐位锚', 'Stage 0 c4', '云机重建标 ANCHOR_PENDING', 'S'),
    ('X22', '20260930_1141_E6l_time_memory_stage/（REPORT 对应 CSV、cards 判别读数机器表）', 'A2-9 source_claim_reconciliation', 'S1', '数值句回查待定', 'S'),
    ('X27', '20260923_0254_E6i_measurement_need_fit/cache/<段>/V_park20_LEGACY__LEGACY_PARK_NAN.*', 'A2-8 V 原值锚（源函数返回 −vol，E6i 取负还原）', 'Stage 0 A2-8', '云机源函数重算只印符号', 'S'),
]


def cache_dir():
    return os.path.join(os.path.dirname(os.path.dirname(M.CODE.rstrip('/'))), 'data', 'cache')


def present_inputs():
    rows = []
    tgz = os.path.join(M.CODE, 'delivery/I11_candidate_pools_v2_20260903/I11_candidate_pools_v2_20260903.tar.gz')
    rows.append(('X23', '<代码目录>/delivery/I11_candidate_pools_v2_20260903/I11_candidate_pools_v2_20260903.tar.gz（git 跟踪）', 'A2-1 云机版锚（六 pool2 + pool1 逐字节）',
                 'Stage 0 A2-1（N）', '无', 'N', M.sha_file(tgz), 'PRESENT'))
    cd = cache_dir()
    for f in sorted(os.listdir(cd)):
        p = os.path.join(cd, f)
        if os.path.isfile(p) and (f.startswith('daily_kline_20') or f.startswith('ftl_')):
            rows.append(('X24', '<用户目录>/data/cache/' + f, 'resonance 缓存（段 / 全程日线；FundamentalTL 六表）', 'build_period / 状态序列 / 全程项', '回落读日线 CSV 并回写缓存（禁止）',
                         'N', M.sha_file(p), 'PRESENT'))
    for root, _, fs in os.walk('/mnt/big/base'):
        if 'trade_date.csv' in fs and 'uqer_adj_refresh' in root:
            rows.append(('X26', '/mnt/big/base/<账号>/script/wash_daily_k/uqer_update/uqer_adj_refresh/trade_date.csv', '交易日历文件（对行情索引）', 'Stage 0 A4-4', '只用行情索引',
                         'N', M.sha_file(os.path.join(root, 'trade_date.csv')), 'PRESENT'))
    kd = glob.glob('/mnt/big/base/*/KLines_make/daily_temp3')
    if kd:
        n = len([f for f in os.listdir(kd[0]) if f.endswith('.csv')])
        rows.append(('X25', '/mnt/big/base/<账号>/KLines_make/daily_temp3/（%d 个日文件）' % n, '日线源 CSV（缓存命中时不读）', '无（缓存命中）', '无', 'N', '', 'PRESENT_NOT_READ'))
    return rows


def build_external():
    out = []
    for x in X:
        xid, rel, use, step, impact, stage = x
        first = rel.split('/')[0]
        exists = os.path.exists(os.path.join('/mnt/sda2', M._names()[0], 'results', first)) if M._names()[0] else False
        out.append(dict(id=xid, path=('results/' + rel), purpose=use, read_step=step, sha256='', status='PRESENT_UNHASHED' if exists else 'SOURCE_WAIT',
                        missing_impact=impact, stage=stage))
    for r in present_inputs():
        out.append(dict(id=r[0], path=r[1], purpose=r[2], read_step=r[3], sha256=r[6], status=r[7], missing_impact=r[4], stage=r[5]))
    df = pd.DataFrame(out)
    df['guard'] = '按 sha 校验，不按路径（纪律 78）'
    return df


SCHEMA = {
    'tier': 'P0_REVIEW | P1_LEDGER | P2_RANDOM | P3_DATA_REF',
    'created_at': 'YYYY-MM-DD HH:MM:SS（机器时间）', 'machine': '别名', 'stage': 'N | S',
    'source_root': '相对根（结果目录或阶段 N 工作目录），不写绝对路径', 'file_count': 'int', 'total_bytes': 'int',
    'files': [{'path': '相对 source_root', 'sha256': '64 hex', 'bytes': 'int', 'rows': 'CSV 行数（表头外）或 -1', 'role': '登记 / 报告 / 账本 / 随机 / 数据引用'}],
    'manifest_sha256': '对 files 列表（按 path 排序、canonical JSON）计算',
}
TIERS = {
    'P0_REVIEW': 'plan / brief / 授权、源合同与可分发源码、全部注册与比较清单、policy 与 query 表、主 72 + 父 + 关键对照逐日收益 / 费用 / 仓位 / size、逐状态账本、随机汇总与种子 / 环境、完整回执和限制',
    'P1_LEDGER': '确定性主 / 附属全部逐日账本、目标 / 实际持仓稀疏索引、关键源快照与状态检查点',
    'P2_RANDOM': '主随机审计路径完整账本、全部随机流复放所需输入与稳定键（大体积可流式充分统计，但须能复跑指定路径）',
    'P3_DATA_REF': '行情 / 因子缓存的允许版本、schema、列血缘、目录相对位置、sha 与缺口表（不复制行情；遵守数据权限）',
}


def manifest(root, paths, tier, role_of):
    files = []
    for p in sorted(paths):
        ap = os.path.join(root, p)
        rows = -1
        if p.endswith('.csv'):
            with open(ap, 'rb') as fh:
                rows = max(sum(1 for _ in fh) - 1, 0)
        files.append(dict(path=p, sha256=M.sha_file(ap), bytes=os.path.getsize(ap), rows=rows, role=role_of(p)))
    body = json.dumps(files, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return dict(tier=tier, created_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE, stage='N', source_root='E6m_stageN 工作目录',
                file_count=len(files), total_bytes=int(sum(f['bytes'] for f in files)), files=files, manifest_sha256=hashlib.sha256(body.encode()).hexdigest())


def role(p):
    return ('登记' if p.startswith(('registry/', 'registration/')) else '报告骨架' if p.startswith('reports_skeleton/') else
            '核验' if p.startswith(('stage0/', 'checks/')) else '回执' if p.startswith('task_status/') else '代码存档' if p.startswith('code_register/') else '其他')


def main():
    W = M.work()
    ext = build_external()
    M.atomic_write_csv(M.P('registry', 'external_inputs_E6m.csv'), ext)
    rdir = M.P('replica')
    os.makedirs(rdir, exist_ok=True)
    for t in TIERS:
        M.atomic_write_json(os.path.join(rdir, 'replica_manifest_%s_schema.json' % t.split('_')[0]), dict(schema=SCHEMA, tier=t, contents=TIERS[t]))
    keep = []
    for root, _, fs in os.walk(W):
        rel_root = os.path.relpath(root, W)
        if rel_root.startswith(('tmp', 'replica', 'attempts', 'logs')) or '/cache_cloud' in '/' + rel_root or 'c2_rebuild_parts' in rel_root or 'anchor_repo_delivery' in rel_root:
            continue
        for f in fs:
            keep.append(os.path.normpath(os.path.join(rel_root, f)))
    man = manifest(W, keep, 'P0_REVIEW', role)
    dd = os.path.join(rdir, 'dryrun', 'P0')
    if os.path.exists(dd):
        raise RuntimeError('dry-run 目录已存在（每次 attempt 保留，不覆盖）')
    for f in man['files']:
        os.makedirs(os.path.dirname(os.path.join(dd, f['path'])), exist_ok=True)
        shutil.copy2(os.path.join(W, f['path']), os.path.join(dd, f['path']))
    bad = [f['path'] for f in man['files'] if M.sha_file(os.path.join(dd, f['path'])) != f['sha256']]
    man['dry_run'] = dict(copied_to='replica/dryrun/P0/', verified=len(man['files']) - len(bad), mismatched=bad)
    M.atomic_write_json(os.path.join(rdir, 'replica_manifest_P0_dryrun.json'), man)
    p3 = [dict(path=r['path'], sha256=r['sha256'], status=r['status']) for r in ext.to_dict('records') if r['id'] in ('X23', 'X24', 'X25', 'X26')]
    M.atomic_write_json(os.path.join(rdir, 'replica_manifest_P3_dataref_stageN.json'), dict(tier='P3_DATA_REF', stage='N', machine=M.MACHINE,
                                                                                            created_at=M.time.strftime('%Y-%m-%d %H:%M:%S'), refs=p3,
                                                                                            note='阶段 N 只记数据引用的 sha；P1 / P2 阶段 N 无账本与随机产物（NOT_APPLICABLE）'))
    readme = ['# E6m 副本包（阶段 N 结构与 dry-run）', '',
              '用途：brief A7 / plan §13.2 的第二副本包。每个主要完成阶段生成 P0–P3 并 sha 验证；缺副本不伪称产物级复核通过。', '',
              '| 档 | 内容 | 阶段 N |', '|---|---|---|']
    for t, c in TIERS.items():
        readme.append('| %s | %s | %s |' % (t, c, {'P0_REVIEW': '本次 dry-run：%d 个文件复制到 dryrun/P0/ 并逐件重算 sha，%d 处不符' % (len(man['files']), len(bad)),
                                                'P1_LEDGER': '无账本（NOT_APPLICABLE）', 'P2_RANDOM': '无随机产物（NOT_APPLICABLE）',
                                                'P3_DATA_REF': '记缓存 / 交付包 / 日历的 sha（replica_manifest_P3_dataref_stageN.json）'}[t]))
    readme += ['', 'manifest 格式见 `replica_manifest_<P0|P1|P2|P3>_schema.json`；`manifest_sha256` = files 列表（按 path 排序的 canonical JSON）的 sha256。',
               '目的地：阶段 N 在云机跑，副本目的地 = 47 恢复后的结果目录（brief A7）；阶段 S 在 47 跑时目的地 = 云机 `factor_runs/resonance/replica/E6m/`。']
    M.atomic_write_text(os.path.join(rdir, 'README.md'), '\n'.join(readme) + '\n')
    ok = not bad
    M.write_receipt(os.environ.get('E6M_TASK', 'N6_replica_external'), [M.P('registry', 'external_inputs_E6m.csv'), os.path.join(rdir, 'README.md'),
                                                                        os.path.join(rdir, 'replica_manifest_P0_dryrun.json'), os.path.join(rdir, 'replica_manifest_P3_dataref_stageN.json')],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__], external_rows=len(ext), p0_files=len(man['files']))
    print(json.dumps(dict(external=len(ext), status=ext.status.value_counts().to_dict(), p0_files=len(man['files']), p0_bytes=man['total_bytes'], mismatched=len(bad)),
                     ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
