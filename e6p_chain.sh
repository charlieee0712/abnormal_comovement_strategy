#!/bin/bash
# E6p 串行链（后台）：bash e6p_chain.sh <链名> <步骤 1> <步骤 2> …；每步 = "日志名:python 参数（逗号分隔）"；任一步失败即停并写 <链名>.failed。
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261020_0905_E6p_state_dependent_holding" && pwd)
NAME="$1"; shift
export E6P_WORK=$W OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache
cd "$C"
rm -f "$W/logs/$NAME.done" "$W/logs/$NAME.failed"
for step in "$@"; do
  log="${step%%:*}"; args="${step#*:}"
  echo "[$(date '+%F %T')] start $log" >> "$W/logs/$NAME.chain.log"
  taskset -c 96-191,288-383 python3 ${args//,/ } > "$W/logs/$log.log" 2>&1
  rc=$?
  echo "[$(date '+%F %T')] end $log rc=$rc" >> "$W/logs/$NAME.chain.log"
  if [ $rc -ne 0 ]; then echo "$log" > "$W/logs/$NAME.failed"; exit $rc; fi
done
date '+%F %T' > "$W/logs/$NAME.done"
