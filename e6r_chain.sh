#!/bin/bash
# E6r 串行链（47 端）：bash e6r_chain.sh <链名> <步骤…>；每步 = 一个 python 脚本 + 参数（用 ':' 分隔参数，如 e6r_run.py:accounts:--phase:A2）；
# 每步写 $W/logs/chain_<链名>_<序号>_<名>.log 与 $W/task_status/chain/<链名>_<序号>_<名>.done / .failed；任一步失败即停（不自动跳过）。
# 可选 E6R_PRE：python 前的包装命令（如 "python3 e6r_membind.py"，只设内存策略后 exec，不改计算）。
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261024_1250_E6r_entry_quality_roles" && pwd)
TAG="$1"; shift
cd "$C"
mkdir -p "$W/logs" "$W/task_status/chain" "$W/tmp/tmpdir" "$W/tmp/numba_cache"
i=0
for step in "$@"; do
  i=$((i+1))
  args=$(echo "$step" | tr ':' ' ')
  name=$(echo "$step" | tr ':/' '__' | cut -c1-60)
  echo "[$(date '+%F %T')] start $TAG $i $name" >> "$W/logs/chain.log"
  E6R_WORK=$W TMPDIR=$W/tmp/tmpdir OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache \
    PYTHONDONTWRITEBYTECODE=1 taskset -c ${E6R_CPUS:-96-191,288-383} ${E6R_PRE} python3 $args > "$W/logs/chain_${TAG}_${i}_${name}.log" 2>&1 < /dev/null
  rc=$?
  if [ $rc -ne 0 ]; then
    echo "[$(date '+%F %T')] FAILED $TAG $i $name rc=$rc" >> "$W/logs/chain.log"
    touch "$W/task_status/chain/${TAG}_${i}_${name}.failed"
    exit $rc
  fi
  touch "$W/task_status/chain/${TAG}_${i}_${name}.done"
  echo "[$(date '+%F %T')] done $TAG $i $name" >> "$W/logs/chain.log"
done
echo "[$(date '+%F %T')] chain $TAG complete" >> "$W/logs/chain.log"
touch "$W/task_status/chain/${TAG}.complete"
