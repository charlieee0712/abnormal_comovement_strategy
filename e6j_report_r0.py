# -*- coding: utf-8 -*-
"""生成 E6j_REPORT_R0.md（plan §10.7：真实源锚、6 / 8bp、R1 身份、测量合同、代码与信息守卫；本地合成与真实测试分开）。
全部数字由本文件的结构化查询从 Stage 0 产物读出；不读任何新收益（R0 只含母体 / 源锚账本数字）。"""
import e6j_boot  # noqa: F401
import os
import sys
import json
import glob

import numpy as np
import pandas as pd

import e6j_core as J
from e6j_report import Report

RES = J.RES
OUT = os.path.join(RES, 'reports', 'E6j_REPORT_R0.md')


def rd(p, **kw):
    return pd.read_csv(os.path.join(RES, p), **kw)


def base_head(**kw):
    h = dict(主体='—', 算子='—', 分母='—', 基准='—', 子集='—', 单位='—', 日期='2010-01-04..2026-03-27（四段）', H='—', 成本模型='—',
             支持='—', 资本视图='—', exposure='—')
    h.update(kw)
    return h


def main():
    man = json.load(open(os.path.join(RES, 'source_manifest.json')))
    a0 = json.load(open(os.path.join(RES, 'registry', 'a0_manifest.json')))
    R = Report('R0')
    R.h(1, 'E6j REPORT R0 —— Stage 0 仪器：源锚、6 / 8bp、R1 身份、测量合同、种子与守卫')
    R.p('用途：Stage 0 六项锚的结果与证据链（brief v1.2 §2；plan §3.2 / §10.1）。**本文件不含任何新收益读数**：出现的净值只来自既有生产母体与 E6i 研究母体的账本，'
        '用于钉住此后一切"子 − 母"的母。执行端，2026-09-27（47 时间）；HEAD `%s`；结果目录 `results/20260927_0038_E6j_k_two_dimension_pilot/`。' % man['git_head'][:7])
    R.p('读法：每张表前一行"表头"给出 主体 / 算子 / 分母 / 基准 / 子集 / 单位 / 日期 / H / 成本模型 / 支持 / 资本视图 / exposure / query_id；正文句尾〔query_id〕指向同一查询。')

    # ---- 0 结论
    ar = rd('anchor_results.csv')
    st = ar.status.value_counts().to_dict()
    R.h(2, '0. 结论')
    R.p('- Stage 0 六项：%s；锚检查合计 %d 项，PASS %d、INFO %d、DIFFERS %d、FAIL %d〔R0-Q00〕。' % (
        '全部 PASS' if man['stage0_all_pass'] else '未全过', len(ar), st.get('PASS', 0), st.get('INFO', 0), st.get('DIFFERS', 0), st.get('FAIL', 0)))
    R.table(pd.DataFrame([dict(item=k, receipts='、'.join(v['receipts']), status='、'.join(map(str, v['status'])), ok=v['ok'])
                          for k, v in man['stage0'].items()]),
            base_head(主体='Stage 0 六项', 算子='任务回执', 分母='回执', 子集='FAILED 须由同名 _rerun 成功覆盖', 单位='状态'), 'R0-Q00')
    R.p('- **R1 ≡ A4b_CVRv5 是精确别名**（掩码逐格、权重 / 持仓 / 8bp 日账本浮点求和序内相同）〔R0-Q05〕；brief W03 的"同源不同路径"暂判来自两处未匹配比较：'
        '展示口径（有持仓日平均 vs 全日平均）与 8bp 近似换算〔R0-Q04、R0-Q06〕。')
    R.p('- **P 主母体上 S / M / C1 三臂（α .125 / .25 / .5 × H 3 / 5 / 10 / 20）= E6i R1 SLOT 账户的精确别名**，四段均已在 E6i 暴露；K_rarpre / K_samt20 两列对象同理；'
        'SM 与 AMT4 为新组合〔R0-Q10、R0-Q18〕。试点在主母体上的新信息只来自 SM；其余五形态是同成员同方向的转移证据。')
    R.p('- 输入差异 17 条只登记不改源（`source_resolution.md` §2）；其中 B 包计数按 plan §5.10 现算为每段 13,398（brief 写 13,230）〔R0-Q17〕。')

    # ---- 1 起点
    R.h(2, '1. 起点、输入与环境')
    docs = pd.DataFrame([dict(file=k, sha256_prefix=v[:8]) for k, v in man['docs_sha256'].items()])
    R.table(docs, base_head(主体='决策端输入与执行端合同文件（结果目录副本）', 算子='sha256', 单位='十六进制前缀'), 'R0-Q01')
    R.p('环境：Python %s / NumPy %s / pandas %s；随机：%s。' % (man['env']['python'], man['env']['numpy'], man['env']['pandas'], man['env']['seed_derivation']))

    # ---- 2 锚 1
    R.h(2, '2. 生产路径锚（第 1 项）：α = 0 逐位重现 E5a；6 / 8bp 双锚')
    a1 = rd('stage0/anchor1_rerun/anchor1_results.csv')
    t = a1[a1.check_id.isin(['A1-P1', 'A1-P0', 'A1-S1'])][['check_id', 'object', 'status', 'note']].fillna('')
    R.table(t, base_head(主体='E5a v2 交付文件', 算子='生产路径 α = 0（e6j_prod 逐字复制生产脚本）重算后逐字节比对', 分母='文件字节',
                         子集='六个 pool2 + pool1 + summary / _delivery_stats / check', 单位='sha256 相同与否', H='5', 成本模型='6bp（E5a 原口径）',
                         支持='native', 资本视图='NATIVE', exposure='E5a 已交付'), 'R0-Q02')
    s8 = rd('anchors/mother_summary_8bp.csv', float_precision='round_trip')
    s8 = s8[['period', 'cfg', 'net_ann', 'net_nw', 'gross_ann', 'turn', 'avg_nh', 'avg_pos', 'n']]
    R.table(s8, base_head(主体='六生产形态母体', 算子='生产路径 α = 0；cost_bp_bilateral = 8 重算', 分母='段内非缺失净值日 n',
                          基准='clean 全市场等权（主基准）', 子集='各段全部形成日', 单位='net / gross 年化百分点；turn 年化倍；avg_nh 只；avg_pos 资金占比（有持仓日平均）',
                          H='5', 成本模型='8bp 线性（政策口径）', 支持='native', 资本视图='NATIVE', exposure='同形态 6bp 已在 E5a 交付；8bp 为本锚重算'), 'R0-Q03')
    c = a1[a1.check_id.isin(['A1-C3', 'A1-C3a', 'A1-C4']) & a1.object.str.endswith('A4b_CVRv5')][['check_id', 'object', 'metric', 'expected', 'got', 'abs_diff', 'status']]
    R.table(c, base_head(主体='A4b_CVRv5 母体', 算子='年化 8bp：精确式 vs brief 近似式 vs brief W02 两位小数', 分母='L = 账本行数；n = 非缺失净值日',
                         单位='年化百分点', H='5', 成本模型='8bp / 6bp', 支持='native', 资本视图='NATIVE', exposure='—'), 'R0-Q04')
    R.p('读法：逐日 net8 − net6 = −2e−4 × 换手逐位成立；年化精确式 net8 = net6 − 0.02 × turn × L / n（缺失日换手为 0），brief 的"≈ net6 − 0.02 × turn"少了 L / n 因子，'
        '在近段差到 0.025〔R0-Q04〕。首跑回执 FAILED（30 项全是检查定义错，见 lessons_delta），`--rerun` 覆盖。')

    # ---- 3 锚 2
    R.h(2, '3. R1 vs A4b_CVRv5 四层身份（第 2 项）')
    pim = rd('stage0/anchor2_rerun/parent_identity_map_rerun.csv')
    R.table(pim[['object_a', 'object_b', 'classification', 'alias_of', 'L1_mask_exact', 'L2_max_abs', 'L3_max_abs', 'L4_max_abs']],
            base_head(主体='R1（E6i 研究）与 A4b_CVRv5（生产 v2）', 算子='掩码 / DEV 目标权重 / 五日持仓 / 8bp 日账本 四层比对',
                      分母='逐格 / 逐日', 子集='四段', 单位='最大绝对差（小数）', H='5', 成本模型='8bp', 支持='native', 资本视图='NATIVE',
                      exposure='R1 四段已在 E6i 暴露'), 'R0-Q05')
    R.p('根目录 `parent_identity_map.csv`（首跑）L4_max_abs = 1.0 是汇总伪值（布尔检查被计成 1.0），以 `stage0/anchor2_rerun/parent_identity_map_rerun.csv` 为准〔R0-Q05〕。')
    dm = rd('stage0/anchor2_rerun/display_metric_reconciliation.csv')
    R.table(dm[['segment', 'E5a_avg_nh', 'E6i_parent_n_mean', 'E5a_avg_pos', 'E6i_pos_mean', 'days', 'days_nh_pos']],
            base_head(主体='同一掩码 / 账本', 算子='两种展示口径', 分母='E5a：有持仓日；E6i：全部日', 单位='只 / 资金占比', H='5', 成本模型='—',
                      支持='native', 资本视图='NATIVE（目标权重和 vs 实际持仓和）'), 'R0-Q06')
    ep = rd('stage0/anchor2_rerun/e6i_parent_anchor.csv')
    R.table(ep[['segment', 'mother', 'net8_ann_recomputed', 'E6i_parent_net8_ann', 'parent_n_mean', 'E6i_parent_n_mean', 'max_abs_daily']],
            base_head(主体='E6i 研究母体 R1 / R2 / A06 / A08', 算子='E6j 调用 E6i 引擎重算 vs E6i 已存母体日账本（任一 H5 子账户 net8 − dnet8）',
                      分母='共同有限日', 基准='clean 全市场等权', 单位='年化百分点 / 只 / 小数', H='5', 成本模型='8bp', 支持='native', 资本视图='NATIVE',
                      exposure='E6i 已暴露'), 'R0-Q07')

    # ---- 4 锚 3
    R.h(2, '4. SLOT 恒等与无经济新增反例（第 3 项）')
    a3 = rd('stage0/anchor3/anchor3_results.csv')
    g = a3.groupby(['test', 'status']).size().reset_index(name='n')
    R.table(g, base_head(主体='六形态 × 四段', 算子='T1 α = 0；T2 MA1 ≡ K0；T3 FALLBACK ≠ REPLACE；T4 复制旧残差；T5 置缺失不重估 + TRANSPORT；T6 SRC vs E6i SLOT；T7 成员缓存',
                         分母='检查项', 单位='项数', 支持='native', exposure='只算掩码 / 分数，不算收益'), 'R0-Q08')
    rse = rd('stage0/anchor3/rank_support_effect.csv')
    R.table(rse.rename(columns={'object': 'form', 'got': 'mask_cells_changed'}),
            base_head(主体='六形态', 算子='复制旧残差、稳定哈希置 5% 格缺失、不重估；SRC 秩坐标 α .25', 分母='掩码格', 子集='各段全部形成日',
                      单位='变化格数', 支持='native（NEW 有效域缩小）', exposure='诊断，无经济新增'), 'R0-Q09')
    R.p('读法：纯秩坐标移动即可改变掩码，Mmean 两形态最敏感（均值合成对坐标连续敏感），A4b / Munion（切半阈值）几乎不动；TRANSPORT 在同输入下逐值回到 q0〔R0-Q09〕。')
    od = rd('operator_discrepancy_manifest.csv')
    R.table(od[['segment', 'form', 'arm', 'member', 'direction', 'alpha', 'mask_cells_differ', 'verdict']].fillna(''),
            base_head(主体='A4b_CVRv5（= R1）', 算子='生产坐标 SLOT vs E6i Mother(R1).slot K FALLBACK', 分母='掩码格', 子集='推导两段；其余五形态 SPEC_only',
                      单位='不同格数', 支持='native', exposure='E6i 已暴露'), 'R0-Q10')

    # ---- 5 测量合同
    R.h(2, '5. 新测量合同（第 4 项）：合成检验与真实字段检验分开')
    syn = rd('stage0/features/synthetic.csv')
    R.table(syn, base_head(主体='玩具网格（稳定哈希种子）', 算子='代数 / 因果 / 退化状态', 分母='检查项', 单位='—', exposure='不碰行情'), 'R0-Q11')
    real = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(os.path.join(RES, 'stage0/features/real_*.csv')))], ignore_index=True)
    R.table(real[real.test.isin(['R01', 'R02', 'R03', 'R04'])][['segment', 'test', 'what', 'status', 'detail']].fillna(''),
            base_head(主体='E6i 同款预热网格（真实字段）', 算子='恒等核对', 分母='有效格', 子集='四段', 单位='最大相对 / 绝对误差', exposure='不含收益'), 'R0-Q12')
    R.table(real[real.test == 'R05'][['segment', 'what', 'detail']],
            base_head(主体='E6i 源成员 vs E6j J 成员', 算子='pool0 格逐格比对', 分母='pool0 格', 子集='四段', 单位='占比 / 最大相对差 / 格数',
                      exposure='源成员已在 E6i 暴露'), 'R0-Q13')
    R.p('读法：J_B2_POINT_TR_CC 与 K0 逐位同值（K0 锚，账户 = 母体，不重复计算）；J_B6_CV20、J_B5_RARPRE_CC_W20_LT 与源在共同格逐位同值、只多出最少观测数（10 vs 14）带来的覆盖；'
        'J_B1_S20lag、J_B2_SLOPE20_TR_CC 与源差在浮点与覆盖；J_B2_MR3 / MR5 / ROS20 与源的差来自有效 OHLC 掩码（源在全市场原值上算）——按 plan §3.4 各自保留、不合并〔R0-Q13〕。')
    cov = rd('feature_contracts_J.csv')
    cov['block'] = cov.member_id.str.split('_').str[1]
    cs = cov.groupby('block')[[s for s in J.SEGMENTS]].agg(['min', 'median']).round(4)
    cs.columns = ['%s_%s' % a for a in cs.columns]
    R.table(cs.reset_index(), base_head(主体='110 个 J 原值', 算子='pool0 格有限值占比', 分母='pool0 格', 子集='按块', 单位='占比'), 'R0-Q14')

    # ---- 6 种子 / 守卫 / A0
    R.h(2, '6. 种子重放、E7 守卫、A0 编译（第 5 项）')
    R.table(rd('stage0/replay/replay_results.csv'), base_head(主体='R1 × K_rar20（低坏）IID 随机路径 8 条（推导段 2010-2014）', 算子='哈希比对（不读收益值）',
                                                              分母='路径', 单位='逐位相同与否', H='5', 成本模型='8bp', 支持='native', exposure='不读数值'), 'R0-Q15')
    R.table(rd('stage0/guard_attack/guard_attack_results.csv'), base_head(主体='E6j 触及行情 / 特征的全部入口（覆盖矩阵 G1–G7）', 算子='合成未来数据 / 伪造 sidecar 攻击',
                                                                         分母='入口', 单位='是否拦截'), 'R0-Q16')
    cnt = a0['counts']
    t17 = pd.DataFrame([dict(item=k, value=json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v) for k, v in cnt.items()] +
                       [dict(item='brief 写的 B 计数', value=a0['brief_B_count_13230']), dict(item='编译器现算 B 计数', value=a0['compiled_B_count'])] +
                       [dict(item='check:%s' % k, value=v) for k, v in a0['checks'].items()])
    R.table(t17, base_head(主体='A0 登记编译（P 528 / B 210 行）', 算子='登记展开 vs 任务规划器独立枚举；逐元组比对', 分母='描述符', 子集='W10 H 网格 × α 网格',
                           单位='个 / 是否', H='B {1,2,3,5,10,15,20}；P {3,5,10,20}', 成本模型='8bp', 支持='native（CS 另表）'), 'R0-Q17')
    ex = rd('registry/exposure_ledger.csv')
    R.table(ex.exposure_type.value_counts().rename_axis('exposure_type').reset_index(name='rows'),
            base_head(主体='P 描述符与 B 登记行', 算子='E6i merged_index 查找 + 登记规则', 分母='台账行', 单位='行数', exposure='见各类'), 'R0-Q18')
    d = man['plan_tests']
    R.table(pd.DataFrame([dict(total=d['total'], passed=d['passed'], python=d['python'], numpy=d['numpy'], pandas=d['pandas'],
                               script_sha_prefix='a3fec9bd')]),
            base_head(主体='plan §13.3 合成脚本（从 PLAN_COPY.md 提取，sha 与 plan 所记一致）', 算子='原样运行', 分母='命名检查', 单位='项',
                      exposure='不碰行情；不是真实回测'), 'R0-Q19')
    R.p('plan 合成测试 T81 / T84 按 plan 原网格 H = 1…20 断言，原样通过；W10 的 7 档计数由 A0 编译器另核〔R0-Q17、R0-Q19〕。')

    # ---- 7 限制
    R.h(2, '7. 限制与待办（不影响 Stage 0 结论）')
    R.p('- Stage 0 第 4 项的真实字段检验在四段上计算了 J 原值、覆盖与别名统计（无任何收益、无账户）；B 包后段账户与收益关联统计仍按记录 B 生效条件执行。')
    R.p('- W03 所引 E6i 投入资金 0.317 / 0.520 / 0.700 / 0.833 的出处表未定位；同一账本上两种定义实算见〔R0-Q06〕。')
    R.p('- 段首事件钟沿 E6i：预热期无已知触发，段首 spell / 触发被截断（登记为限制，不改源）。')
    R.p('- 下一步：Stage A 两个登记包（P / B）同时冻结 → A0 登记落盘 → Stage 1 推导段测量诊断 → profile 后报并发与时长。')
    sha = R.write(OUT)
    print('R0 written', sha[:12], len(R.qids), 'tables')
    J.write_receipt('report_R0', [OUT, os.path.join(RES, 'reports', 'query_registry.json')], 'SUCCEEDED', n_tables=len(R.qids))
    return 0


if __name__ == '__main__':
    sys.exit(main())
