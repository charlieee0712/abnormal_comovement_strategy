#!/bin/bash
# E6q 串行链（47 端）：bash e6q_chain.sh <步骤…>；每步 = 一个 python 脚本 + 参数（用 ':' 分隔参数，如 e6q_run.py:accounts:--phase:A2）；
# 每步写 $W/logs/chain_<序号>_<名>.log 与 .done / .failed 标记；任一步失败即停（不自动跳过）。
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261023_0040_E6q_sell_reinvest_split" && pwd)
cd "$C"
mkdir -p "$W/logs" "$W/task_status/chain"
i=0
for step in "$@"; do
  i=$((i+1))
  args=$(echo "$step" | tr ':' ' ')
  name=$(echo "$step" | tr ':/' '__' | cut -c1-60)
  echo "[$(date '+%F %T')] start $i $name" >> "$W/logs/chain.log"
  E6Q_WORK=$W OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache \
    taskset -c 96-191,288-383 python3 $args > "$W/logs/chain_${i}_${name}.log" 2>&1 < /dev/null
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "[$(date '+%F %T')] FAILED $i $name rc=$rc" >> "$W/logs/chain.log"
    touch "$W/task_status/chain/${i}_${name}.failed"
    exit $rc
  fi
  touch "$W/task_status/chain/${i}_${name}.done"
  echo "[$(date '+%F %T')] done $i $name" >> "$W/logs/chain.log"
done
echo "[$(date '+%F %T')] chain complete" >> "$W/logs/chain.log"
