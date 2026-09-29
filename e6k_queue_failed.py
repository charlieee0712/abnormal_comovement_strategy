# -*- coding: utf-8 -*-
"""E6k 补跑队列：首轮与增补队列文件里回执不是 SUCCEEDED 的行（按回执名判断，不按 worker_done 的 rc 行），原样写成补跑队列。
用法：python3 e6k_queue_failed.py <pkg> <out>。只写队列文本，不跑任何东西；补跑任务与首轮同一代码版本（恢复路径只作用于主路径复核失败的日）。"""
import os
import sys
import glob

import e6k_core as K
import e6k_seal as SEAL


def main():
    pkg, out = sys.argv[1], sys.argv[2]
    st = SEAL.receipts(pkg)
    lines = []
    for f in [K.P('logs', 'queue_%s.txt' % pkg)] + sorted(glob.glob(K.P('logs', 'queue_topup_%s_*.txt' % pkg))):
        if not os.path.exists(f):
            continue
        for line in open(f, encoding='utf-8'):
            w = line.split()
            if not w:
                continue
            mother, meas = w[2].split('|')
            if w[0] == 'det':
                name = 'run_det_%s_%s__%s' % (w[1], mother, meas)
            else:
                name = 'run_rand_%s_%s_%s__%s__p%d_%d' % (w[3], w[1], mother, meas, int(w[4]), int(w[5]))
            if st.get(name) != 'SUCCEEDED':
                lines.append(line.strip())
    lines = list(dict.fromkeys(lines))
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + ('\n' if lines else ''))
    print(len(lines), 'rerun lines', flush=True)


if __name__ == '__main__':
    main()
