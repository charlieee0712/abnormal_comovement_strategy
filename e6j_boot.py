# -*- coding: utf-8 -*-
"""E6j 进程启动钩子 —— 入口脚本的第一个 import（在 numpy / pandas / pyarrow 之前）。
与 e6i_boot 相同的两项进程设置（抄技术，不 import 上一轮模块）：pyarrow 不起 S3 线程；BLAS / OMP 线程上限 4（brief §14）。
"""
import os
import sys

sys.modules.setdefault('pyarrow._s3fs', None)
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_MAX_THREADS'):
    os.environ.setdefault(_k, '4')
