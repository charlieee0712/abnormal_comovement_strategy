#!/bin/bash
# E6o 后台启动器：bash e6o_bg.sh <日志名> <python 脚本与参数…>
# 固定：E6O_WORK、核心绑定 96-191,288-383、BLAS 4、NUMBA 1；setsid + nohup，脱离会话；日志写 $E6O_WORK/logs/<日志名>.log
C0=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C0/../../results/20261017_2138_E6o_account_exit_stage" && pwd)
C=$(cd "$(dirname "$0")" && pwd)
NAME="$1"; shift
mkdir -p "$W/logs"
cd "$C"
E6O_WORK=$W OMP_NUM_THREADS=${OMP_NUM_THREADS:-4} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4} MKL_NUM_THREADS=${MKL_NUM_THREADS:-4} \
NUMBA_NUM_THREADS=${NUMBA_NUM_THREADS:-1} setsid nohup taskset -c 96-191,288-383 python3 "$@" > "$W/logs/$NAME.log" 2>&1 < /dev/null &
echo "started $NAME pid=$!"
