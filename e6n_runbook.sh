#!/usr/bin/env bash
# E6n 运行手册（47；brief §5 S5–S7；方式 B）。用法：bash e6n_runbook.sh <步> [参数]。任何读收益的步骤都由模块自身的守卫拦（推导段 deriv_ready：冻结 + seal_B1_0；后段 post_gate）。
# 并发：账户每 (段, 母体) 一进程；随机每段一个父进程 + fork 池（--workers）；资源：taskset 96-191,288-383、BLAS 4、NUMBA 1、ulimit -u 4096。
set -uo pipefail
: "${E6N_WORK:?E6N_WORK 未设}"
RD=$E6N_WORK
C=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd); cd "$C"
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-4} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4} MKL_NUM_THREADS=${MKL_NUM_THREADS:-4} NUMBA_NUM_THREADS=1
ulimit -u 4096
PIN=(taskset -c 96-191,288-383)
FORMS8="A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5 R2 A06"
FORMS6="A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5"
mkdir -p "$RD/logs"

accounts() {   # accounts <段...>：每 (段, 母体) 一进程，后台；只打印 PID
  for s in "$@"; do for f in $FORMS8; do
    nohup "${PIN[@]}" python3 e6n_accounts.py --seg "$s" --parent "$f" > "$RD/logs/acc_${s}_${f}.log" 2>&1 &
    echo "acc $s $f $!"
  done; done
}

randoms() {    # randoms <段> <workers> [path0 npaths groups mechs]
  local s=$1 w=$2 p0=${3:-0} np=${4:-1024} g=${5:-} m=${6:-CONTENT_IID,CONTENT_ISK_P5,CONTENT_QRANGE_P5,R_MEMORY,LEGACY_POLICY_RANDOM}
  local tag="${s}_p${p0}_${np}"
  nohup "${PIN[@]}" python3 e6n_rand.py run --seg "$s" --workers "$w" --path0 "$p0" --npaths "$np" --mechs "$m" --claim ${g:+--groups "$g"} > "$RD/logs/rand_${tag}_$(date +%H%M%S).log" 2>&1 &
  echo "rand $tag $!"
}

support() {    # support <段...>
  for s in "$@"; do for f in $FORMS6; do
    nohup "${PIN[@]}" python3 e6n_support.py --seg "$s" --form "$f" > "$RD/logs/sup_${s}_${f}.log" 2>&1 &
    echo "sup $s $f $!"
  done; done
}

b2() {         # b2 <段...>：每 (段, 形态) 一进程（六形态并行）
  for s in "$@"; do for f in $FORMS6; do
    nohup "${PIN[@]}" python3 e6n_b2_run.py --seg "$s" --forms "$f" > "$RD/logs/b2run_${s}_${f}.log" 2>&1 &
    echo "b2 $s $f $!"
  done; done
}

stats() {      # stats <out> <段...>（desc / cmp / rand 逐段，前台顺序）
  local out=$1; shift
  for s in "$@"; do
    "${PIN[@]}" python3 e6n_stats.py desc --seg "$s" --out "$out" || return 1
    "${PIN[@]}" python3 e6n_stats.py cmp --seg "$s" --out "$out" || return 1
    "${PIN[@]}" python3 e6n_stats.py rand --seg "$s" --out "$out" || return 1
  done
}

case "${1:-}" in
  accounts) shift; accounts "$@" ;;
  randoms) shift; randoms "$@" ;;
  support) shift; support "$@" ;;
  b2) shift; b2 "$@" ;;
  stats) shift; stats "$@" ;;
  *) echo "用法：$0 accounts|randoms|support|b2|stats …"; exit 2 ;;
esac
