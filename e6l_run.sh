#!/bin/bash
# E6l 运行包装：核绑定 + BLAS ≤ 4 + 日志脱敏（家目录 / conda 环境名一律替换；不写任何账号名）
# 用法：e6l_run.sh <日志路径> <python 参数...>
LOG="$1"; shift
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4 PYTHONUNBUFFERED=1
export PYTHONPATH=/mnt/sda2/lichenchen/code/project_core
export NUMBA_CACHE_DIR=/mnt/sda2/lichenchen/tmp/e6l_numba_cache
mkdir -p "$(dirname "$LOG")"
taskset -c 96-191,288-383 python3 "$@" 2>&1 | sed -u -E 's#/home/[^/[:space:]]+#<HOME>#g; s#envs/[^/[:space:]]+#envs/<ENV>#g' > "$LOG"
exit ${PIPESTATUS[0]}
