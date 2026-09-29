# -*- coding: utf-8 -*-
"""E6k 进程启动钩子 —— 入口脚本的第一个 import（在 numpy / pandas / pyarrow / polars / numba 之前）。
沿 e6j_boot 两项（pyarrow 不起 S3 线程；BLAS / OMP 线程上限 4，brief §8）；另：
  POLARS_MAX_THREADS 默认 2、NUMBA_NUM_THREADS 默认 1（进程级并发为主，避免核内超订）；
  私有包目录 /mnt/sda2/lichenchen/pylib/e6k（用户 2026-09-28 同意安装；pip --target，不改共享 conda 环境）
  追加在 sys.path 末尾：只提供 polars，不遮蔽任何已装包。"""
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
