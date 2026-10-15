#!/usr/bin/env bash
# E6n 链式编排（47；方式 B 已授权的连续步骤，断网不影响）：用法 bash e6n_chain.sh deriv_close <pid…> | post_launch | post_close <pid…>
#   deriv_close：等推导段随机父进程退出 → 推导段统计（desc / cmp / rand）→ MC 增补循环（512 一批，≤ 8,192）→ seal deriv → 生效条件回执 → part1
#   post_launch：生效条件回执 all_pass 才启动后段：账户 16、支持桥 12、随机两段（认领模式，可多父进程）；账户 / 支持完成后再起 B2（每形态一进程）/ B3 / B4 / 分解
#   post_close：等后段随机退出 → 后段统计 → MC 增补 → seal post → full 统计 / 政策 / bootstrap / B5 / B6 / 合表
# 日志 logs/chain_<步>.log；每步失败即停（不跳步）。
set -uo pipefail
: "${E6N_WORK:?E6N_WORK 未设}"
RD=$E6N_WORK
C=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd); cd "$C"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=1
ulimit -u 4096
PIN=(taskset -c 96-191,288-383)
LOG="$RD/logs/chain_${1:-x}.log"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
run() { log "RUN $*"; "${PIN[@]}" "$@" >> "$LOG" 2>&1 || { log "FAIL rc=$? : $*"; exit 1; }; }
waitpids() { for p in "$@"; do while kill -0 "$p" 2>/dev/null; do sleep 60; done; done; }

topup_loop() {   # topup_loop <out> <workers> <段…>
  local out=$1 w=$2; shift 2
  for round in 1 2 3 4 5 6 7 8 9 10 11 12 13 14; do
    local any=0
    for s in "$@"; do
      run python3 e6n_stats.py rand --seg "$s" --out "$out"
      local plan="$RD/$out/mc_plan_$s.csv"
      local todo
      todo=$(python3 -c "
import pandas as pd
P = pd.read_csv('$plan', keep_default_na=False)
P = P[pd.to_numeric(P.get('topup', 0), errors='coerce').fillna(0) > 0] if 'topup' in P else P.iloc[:0]
for (m, h), g in P.groupby(['mechanism', 'have']):
    print('%s %d %s' % (m, int(h), ','.join(sorted(set(g.group)))))
")
      if [ -n "$todo" ]; then
        any=1
        while read -r m h groups; do
          [ -z "$m" ] && continue
          [ "$h" -ge 8192 ] && continue
          log "TOPUP $s $m path0=$h groups=$groups"
          run python3 e6n_rand.py run --seg "$s" --workers "$w" --mechs "$m" --groups "$groups" --path0 "$h" --npaths 512 --claim
        done <<< "$todo"
      fi
    done
    [ $any -eq 0 ] && { log "MC 计划无增补（round $round）"; return 0; }
  done
  log "MC 增补轮数用尽"
}

case "${1:-}" in
  deriv_close)
    shift
    log "等推导段随机父进程 $*"
    waitpids "$@"
    for s in 2010-2014 2015-2018; do
      run python3 e6n_stats.py desc --seg "$s" --out results/deriv
      run python3 e6n_stats.py cmp --seg "$s" --out results/deriv
    done
    topup_loop results/deriv 64 2010-2014 2015-2018
    run python3 e6n_seal.py seal deriv
    run python3 e6n_s0_rest.py close
    run python3 e6n_stage_b.py conditions
    run python3 e6n_reports.py part1
    log "DERIV_CLOSE_DONE"
    ;;
  post_launch)
    python3 -c "import json,sys; sys.exit(0 if json.load(open('$RD/registration/record_B_conditions_receipt_E6n.json')).get('all_pass') else 1)" || { log "生效条件未全过：不启动后段"; exit 2; }
    for s in 2019-2023 2024-2026; do
      for f in A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5 R2 A06; do
        nohup "${PIN[@]}" python3 e6n_accounts.py --seg "$s" --parent "$f" > "$RD/logs/acc_${s}_${f}.log" 2>&1 &
        echo $! >> "$RD/logs/post_acc.pids"
      done
      for f in A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5; do
        nohup "${PIN[@]}" python3 e6n_support.py --seg "$s" --form "$f" > "$RD/logs/sup_${s}_${f}.log" 2>&1 &
        echo $! >> "$RD/logs/post_acc.pids"
      done
    done
    nohup "${PIN[@]}" python3 e6n_rand.py run --seg 2019-2023 --workers 40 --claim > "$RD/logs/rand_2019-2023_p0_1024.log" 2>&1 &
    echo $! > "$RD/logs/post_rand.pids"
    nohup "${PIN[@]}" python3 e6n_rand.py run --seg 2024-2026 --workers 26 --claim > "$RD/logs/rand_2024-2026_p0_1024.log" 2>&1 &
    echo $! >> "$RD/logs/post_rand.pids"
    log "后段账户 / 支持 / 随机已启动"
    waitpids $(cat "$RD/logs/post_acc.pids")
    log "后段账户 / 支持完成"
    nohup "${PIN[@]}" python3 e6n_rand.py run --seg 2019-2023 --workers 14 --claim > "$RD/logs/rand_2019-2023_p0_1024_b.log" 2>&1 &
    echo $! >> "$RD/logs/post_rand.pids"
    for s in 2019-2023 2024-2026; do
      for f in A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5; do
        nohup "${PIN[@]}" python3 e6n_b2_run.py --seg "$s" --forms "$f" > "$RD/logs/b2run_${s}_${f}.log" 2>&1 &
      done
      nohup "${PIN[@]}" python3 e6n_b3.py --seg "$s" > "$RD/logs/b3_$s.log" 2>&1 &
      nohup "${PIN[@]}" python3 e6n_b4.py --seg "$s" > "$RD/logs/b4_$s.log" 2>&1 &
      for t in fourway cdose mchm; do
        nohup "${PIN[@]}" python3 e6n_decomp.py $t --seg "$s" > "$RD/logs/decomp_${t}_$s.log" 2>&1 &
      done
    done
    log "POST_LAUNCH_DONE"
    ;;
  post_close)
    shift
    log "等后段随机父进程 $*"
    waitpids "$@"
    for s in 2019-2023 2024-2026; do
      run python3 e6n_stats.py desc --seg "$s" --out results/full
      run python3 e6n_stats.py cmp --seg "$s" --out results/full
    done
    topup_loop results/full 90 2019-2023 2024-2026
    for s in 2010-2014 2015-2018; do
      for f in descriptor_stats comparison_stats random_refs mc_plan; do cp -p "$RD/results/deriv/${f}_$s.csv" "$RD/results/full/${f}_$s.csv"; done
    done
    run python3 e6n_seal.py seal post
    run python3 e6n_stats.py full --out results/full
    run python3 e6n_policy.py
    run python3 e6n_bootstrap.py
    log "POST_CLOSE_DONE"
    ;;
  *) echo "用法：$0 deriv_close <pid…> | post_launch | post_close <pid…>"; exit 2 ;;
esac
