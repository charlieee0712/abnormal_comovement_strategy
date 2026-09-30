# -*- coding: utf-8 -*-
"""E6l 进程启动钩子 —— 入口脚本的第一个 import（在 numpy / pandas / pyarrow / polars / numba 之前）。
沿 e6k_boot：pyarrow 不起 S3 线程；BLAS / OMP 线程上限 4（brief W14）；NUMBA_NUM_THREADS 默认 1（进程级并发为主）；
私有包目录 /mnt/sda2/lichenchen/pylib/e6k（E6k 执行端私装 polars；追加在 sys.path 末尾，不遮蔽已装包；本轮不依赖 polars，
全部计算有纯 numpy / numba 实现）。"""
import os
import sys

sys.modules.setdefault('pyarrow._s3fs', None)
for _k in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_MAX_THREADS'):
    os.environ.setdefault(_k, '4')
os.environ.setdefault('POLARS_MAX_THREADS', '2')
os.environ.setdefault('NUMBA_NUM_THREADS', '1')
_PYLIB = '/mnt/sda2/lichenchen/pylib/e6k'
if os.path.isdir(_PYLIB) and _PYLIB not in sys.path:
    sys.path.append(_PYLIB)
