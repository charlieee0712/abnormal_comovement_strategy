#!/bin/bash
# E6o Stage 0 链：面板补列 → A1 注册表编译（草稿）→ Stage 0 第一部分。日志各自写 logs/。
set -u
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261017_2138_E6o_account_exit_stage" && pwd)
export E6O_WORK=$W OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache
cd "$C"
taskset -c 96-191,288-383 python3 e6o_panels.py > $W/logs/panels3.log 2>&1 || { echo "panels FAILED"; exit 1; }
taskset -c 96-191,288-383 python3 e6o_registry.py > $W/logs/registry.log 2>&1 || { echo "registry FAILED"; exit 1; }
taskset -c 96-191,288-383 python3 e6o_stage0.py --workers 48 > $W/logs/stage0.log 2>&1 || { echo "stage0 FAILED"; exit 1; }
echo "chain_s0 done $(date '+%F %T')"
