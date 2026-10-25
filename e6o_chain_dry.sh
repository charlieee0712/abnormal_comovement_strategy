#!/bin/bash
# E6o 空跑链（seal_A2 之后；假数据：后段日行 = 推导段日行循环复制，不读任何后段结果）：统计 → 随机汇总 / 政策 → 报告 → 推导段恒等预测。输出只写 tmp/dryrun/。
set -u
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261017_2138_E6o_account_exit_stage" && pwd)
export E6O_WORK=$W OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache
cd "$C"
PIN="taskset -c 96-191,288-383"
for s in "stats:python3 e6o_stats.py --phase A2 --dryrun --fake_post" "policy:python3 e6o_policy.py --phase A2 --dryrun --fake_post" \
         "reports:python3 e6o_reports.py --root $W/tmp/dryrun" "ident:python3 e6o_closure.py identities deriv"; do
  n=${s%%:*}; cmd=${s#*:}
  echo "[$(date '+%F %T')] dry_$n start"
  $PIN $cmd > "$W/logs/dry_$n.log" 2>&1 || { echo "[$(date '+%F %T')] dry_$n FAILED"; exit 1; }
  echo "[$(date '+%F %T')] dry_$n ok"
done
echo "chain_dry done $(date '+%F %T')"
