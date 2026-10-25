#!/bin/bash
# E6q 后台启动器：bash e6q_bg.sh <日志名> <python 脚本与参数…>
# 固定：E6Q_WORK（相对代码目录解析，不写含用户目录的绝对路径）、核心绑定 96-191,288-383、BLAS 2、NUMBA 1；setsid + nohup；日志写 $E6Q_WORK/logs/<日志名>.log
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261023_0040_E6q_sell_reinvest_split" && pwd)
NAME="$1"; shift
mkdir -p "$W/logs"
cd "$C"
E6Q_WORK=$W OMP_NUM_THREADS=${OMP_NUM_THREADS:-2} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-2} MKL_NUM_THREADS=${MKL_NUM_THREADS:-2} \
NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache setsid nohup taskset -c 96-191,288-383 python3 "$@" > "$W/logs/$NAME.log" 2>&1 < /dev/null &
echo "started $NAME pid=$!"
