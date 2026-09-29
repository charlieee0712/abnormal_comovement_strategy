# -*- coding: utf-8 -*-
"""E6k 队列生成：确定性任务（段 × 母体 × 测量）+ 随机分片（段 × 任务 × 机制 × 路径区间）；重任务在前（LPT）。只写队列文本，不跑任何东西。"""
import sys

import pandas as pd

import e6k_core as K


def main():
    segs = sys.argv[1].split(',')
    out = sys.argv[2]
    D = pd.read_csv(K.P('registry', 'descriptors_E6k.csv'))
    RR = pd.read_csv(K.P('registry', 'randoms_E6k.csv'))
    RR = RR[RR.alias_of.isna()]
    lines = []
    for s in segs:
        for t, g in D.groupby('task'):
            lines.append(('det %s %s' % (s, t), 1e6 + len(g)))              # 确定性任务排最前（先落盘可核）
        for (t, m), g in RR.groupby(['task', 'mechanism']):
            mother, meas = t.split('|')
            heavy = meas in ('S', 'M', 'Q', 'C1') and m in ('LEGACY_POLICY_RANDOM', 'NEW_COND_ISK_P5')
            if heavy:
                w = 2.3 if mother.startswith('A4b') else (1.7 if mother in ('M_mean3_v2', 'M_mean3_v2_CVRv5', 'M_union3_v2', 'M_union3_v2_CVRv5') else 0.8)
                for p0 in range(0, 1024, 256):
                    lines.append(('rand %s %s %s %d 256' % (s, t, m, p0), w * 256))
            elif m == 'NEW_COND_ISK_IID':
                for p0 in range(0, 1024, 512):
                    lines.append(('rand %s %s %s %d 512' % (s, t, m, p0), 0.5 * 512))
            else:
                lines.append(('rand %s %s %s 0 1024' % (s, t, m), 0.12 * 1024))
    lines.sort(key=lambda x: -x[1])
    with open(out, 'w') as fh:
        for l, _ in lines:
            fh.write(l + '\n')
    print(len(lines), 'lines')


if __name__ == '__main__':
    main()
