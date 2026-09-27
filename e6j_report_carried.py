# -*- coding: utf-8 -*-
"""生成 E6j_REPORT_carried.md（plan §10.7 / §7.7；brief §10）：C1 N×B 三视图重报、领导六形态资本分解、E04 补记、信号描述面板、实施限制。"""
import e6j_boot  # noqa: F401
import os
import sys
import glob

import numpy as np
import pandas as pd

import e6j_core as J
from e6j_report import Report

RES = J.RES
CAR = os.path.join(RES, 'carried')


def head(**kw):
    h = dict(主体='—', 算子='—', 分母='—', 基准='—', 子集='—', 单位='年化百分点', 日期='2010-01-04..2026-03-27（四段）', H='5', 成本模型='8bp 线性',
             支持='native', 资本视图='NATIVE', exposure='E6i 已暴露（carried 重报）')
    h.update(kw)
    return h


def main():
    R = Report('carried')
    R.h(1, 'E6j REPORT carried —— C1 N×B 资本三视图、领导六形态资本分解、E04 补记、信号面板')
    R.p('用途：brief §10 的 carried 四项。C1 只在 E6i 已冻结的 N × 行业宽度 B 配置上重报三个资本视图（不另选 N / B 赢家）；领导表只重算生产 v2 六形态；'
        'E04 不重跑；信号线只复用 E6i 描述面板。**领导表数字对外须用户过目；措辞用"投入资金上升"。**')
    # ---- C1
    R.h(2, '1. C1：N × B（E6i 冻结配置）的 NATIVE / MATCH-CAP / ATTRIBUTION')
    fs = sorted(glob.glob(os.path.join(CAR, 'C1', '*', 'c1_capital_views_*.csv')))
    if fs:
        c = pd.concat([pd.read_csv(p) for p in fs], ignore_index=True)
        an = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(os.path.join(CAR, 'C1', '*', 'c1_native_anchor_*.csv')))], ignore_index=True)
        R.p('NATIVE 锚：重建的 %d 个配置日账本对 E6i 已存 net8 的最大绝对差 %.3g（缺 E6i 对照 %d 个）〔CAR-Q01〕。' % (
            len(an), float(an.max_abs.max()), int(an.max_abs.isna().sum())))
        g = c.groupby(['segment', 'contrast', 'fixed', 'scope']).agg(pairs=('native_d_ann', 'size'), native=('native_d_ann', 'median'),
                                                                      same_capital=('samecap_d_ann', 'median'), attr_unit=('attr_unit_ann', 'median'),
                                                                      attr_deploy=('attr_deploy_ann', 'median'), attr_onesided=('attr_onesided_ann', 'median'),
                                                                      strict_native=('strict_native_d_ann', 'median'),
                                                                      strict_same_capital=('strict_samecap_d_ann', 'median'),
                                                                      matched_capital_share=('matched_capital_share', 'median')).reset_index()
        R.table(g, head(主体='R1 / R2 / A06 × q × 分配 × 64 seed 的配对（中位）', 算子='B16−B8（固定 N）/ N250−N100（固定 B）',
                        分母='部署视图 = 全日历；严格视图 = 两配置共同可行日', 资本视图='NATIVE / MATCH-CAP（逐形成日共同资本）/ ATTRIBUTION（单位资金 + 部署量 + 单边日）',
                        子集='E6i 冻结的 N × B 配置'), 'CAR-Q01')
        R.p('读法：MATCH-CAP 与 NATIVE 的差 = 投入资金差带来的部分；ATTRIBUTION 的单位资金项与部署量项逐日相加 = 两边都有仓位日的 gross 差，只一边有仓位的日子单列；'
            '"同资本后 ≈ 0"须看区间，不预设〔CAR-Q01〕。')
    else:
        R.p('C1 三视图尚未完成（队列在 B 随机之后）。')
    # ---- 领导表
    R.h(2, '2. 领导六形态资本分解（生产 v2 母体）')
    ld = pd.read_csv(os.path.join(CAR, 'leader_six_forms_capital.csv'))
    R.table(ld, head(主体='生产 v2 六形态母体（A4b / Mmean_v2 / Munion_v2 × 纯净 / +CVRv5）', 算子='生产路径 α = 0（锚 1 逐位 = E5a）',
                     分母='全日历；单位资金项只在仓位 > 0 日', 基准='clean 全市场等权', 单位='投入资金 = 目标权重和 / 实际仓位；年化百分点；年化换手倍；只',
                     成本模型='8bp（另列 6bp 总净值供对 E5a）', 资本视图='名义投入资金 / 单位资金 / 总额', exposure='E5a 已交付（6bp）'), 'CAR-Q02')
    R.p('投入资金上升时总超额随之上升；单位资金 gross / net 列回答"选得更好"与"投得更多"的区分〔CAR-Q02〕。对外数字须用户过目。')
    # ---- E04
    R.h(2, '3. E04 补记（E6i RULING 第 17 项；不重跑）')
    e1 = pd.read_csv(os.path.join(CAR, 'E04_two_draws.csv'))
    R.table(e1, head(主体='E6i random_state 焦点臂（RO FOCAL_NEW gap_pos / gap_neg、RS FOCAL_NEW）', 算子='两次抽样：Stage 2 账户 vs carried C2 子账户',
                     分母='臂数', 单位='d_net8_ann 中位（年化百分点）/ 逐臂最大差', 资本视图='NATIVE', exposure='E6i 已暴露'), 'CAR-Q03')
    e2 = pd.read_csv(os.path.join(CAR, 'E04_part1_Q4_recheck.csv'))
    R.table(e2, head(主体='E6i part1 Q4 句"真实状态并不优于随机状态"', 算子='推导两段 × 正 / 负跳空：real_state 中位 vs 两次 random_state 中位',
                     单位='年化百分点 / 布尔', 日期='2010-01-04..2018-12-31', exposure='E6i 已暴露'), 'CAR-Q04')
    nb1, nb2 = int(e2.real_not_better_draw1.sum()), int(e2.real_not_better_draw2.sum())
    R.p('复核：该句在第一次抽样下 %d / 4 格成立、第二次抽样下 %d / 4 格成立；不成立的格随抽样改变——原句对随机臂的具体抽样敏感。'
        '原因：E6i 以 `abs(hash(descriptor_id))` 取随机状态且未设 PYTHONHASHSEED（E04）；E6j 随机层全部改为稳定哈希键〔CAR-Q04〕。' % (nb1, nb2))
    # ---- 信号
    R.h(2, '4. 信号线（只复用描述面板）')
    sg = pd.read_csv(os.path.join(CAR, 'signal_panel_reuse.csv'))
    R.table(sg, head(主体='E6i C3 signal_margin_profile', 算子='复用（不建新阈值账户）', 单位='文件 / sha256', exposure='E6i R0 §9'), 'CAR-Q05')
    R.h(2, '5. 实施限制')
    R.p('- 影子库存账户（ideal / X1）只对 P 主对象与母体做 H5（part3 §11）；买卖标志缺失按"可成交"处理（源默认 unknown_tradable = True）。')
    R.p('- 冲击为源平方根模型的事后加性成本，不改库存；κ 与 A 是情景，不是已确认的实际资金或容量。')
    out = os.path.join(RES, 'reports', 'E6j_REPORT_carried.md')
    sha = R.write(out)
    J.write_receipt('report_carried', [out], 'SUCCEEDED', n_tables=len(R.qids), c1_included=bool(fs))
    print('carried', sha[:12])
    return 0


if __name__ == '__main__':
    sys.exit(main())
