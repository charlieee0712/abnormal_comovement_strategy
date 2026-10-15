#!/usr/bin/env bash
# E6n 自动接力（47；方式 B 已授权的连续步骤，断网不影响；接在 e6n_chain.sh deriv_close 之后）。用法：bash e6n_pipeline.sh <起点> [deriv_close 链 PID]
#   起点 = wait_deriv | post_launch | post_close | finish；从起点顺序做到 finish；每步失败即停（不跳步）；日志 logs/pipeline.log
#   wait_deriv ：等推导段收尾链退出；生效条件回执 all_pass 才往下（part1 若未出只补跑、不阻断）
#   post_launch：账户 16 + 支持桥 12（后台）；随机 2019-2023（58 workers）/ 2024-2026（28 workers），认领模式；账户 / 支持完成 → B2 每形态 / B3 / B4 / 分解（后台）；
#                2024-2026 随机先完而 2019-2023 尚余 ≥ 28 个未认领分片 → 再起一个 2019-2023 认领父进程（28 workers）
#   post_close ：等全部后段随机父进程 → 首 1,024 缺回执分片补跑（非认领单父进程）→ 后段统计 desc / cmp → MC 增补（90 workers）
#                → 推导段统计拷入 results/full → seal post → full 统计 / 政策 / bootstrap
#   finish     ：等 B2 / B3 / B4 / 分解 / 补齐表全部退出（penalty / rawledger 缺则补跑）→ B5 / B6 → 合表 → query（full）→ 补齐表（all_post）
#                → 报告 → 执行端说明 → SCHEMA / 代码登记 / 副本 → 闭包门
# 并发上限：用户 10-15 允许必要时 96 workers（只给随机这一重阶段）；BLAS 4、NUMBA 1、taskset 96-191,288-383、ulimit -u 4096。
set -uo pipefail
: "${E6N_WORK:?E6N_WORK 未设}"
RD=$E6N_WORK
C=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd); cd "$C"
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=1
ulimit -u 4096
PIN=(taskset -c 96-191,288-383)
LOG="$RD/logs/pipeline.log"
FORMS6="A4b A4b_CVRv5 M_mean3_v2 M_mean3_v2_CVRv5 M_union3_v2 M_union3_v2_CVRv5"
FORMS8="$FORMS6 R2 A06"
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
run() { log "RUN $*"; "${PIN[@]}" "$@" >> "$LOG" 2>&1 || { log "FAIL rc=$? : $*"; exit 1; }; }
soft() { log "RUN(soft) $*"; "${PIN[@]}" "$@" >> "$LOG" 2>&1 || log "SOFT_FAIL rc=$? : $*"; }
waitpids() { for p in "$@"; do while kill -0 "$p" 2>/dev/null; do sleep 60; done; done; }
waitfile() { while :; do local any=0; for p in $(cat "$1" 2>/dev/null); do kill -0 "$p" 2>/dev/null && any=1; done; [ $any -eq 0 ] && return 0; sleep 60; done; }
bg() { local tag=$1 pf=$2; shift 2; nohup "${PIN[@]}" "$@" > "$RD/logs/$tag.log" 2>&1 & echo $! >> "$pf"; log "BG $tag pid $!"; }

topup_loop() {   # topup_loop <out> <workers> <段…>（同 e6n_chain.sh）
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

stage_wait_deriv() {
  local cp=$1
  log "等推导段收尾链 $cp"
  waitpids "$cp"
  if grep -q DERIV_CLOSE_DONE "$RD/logs/chain_deriv_close.log"; then log "推导段收尾链完成"; else log "推导段收尾链未写 DERIV_CLOSE_DONE（看 chain_deriv_close.log）"; fi
  python3 -c "import json,sys; sys.exit(0 if json.load(open('$RD/registration/record_B_conditions_receipt_E6n.json')).get('all_pass') else 1)" \
    || { log "生效条件回执缺失或未全过：不启动后段"; exit 2; }
  grep -q DERIV_CLOSE_DONE "$RD/logs/chain_deriv_close.log" || soft python3 e6n_reports.py part1
  log "STAGE_DONE wait_deriv"
}

stage_post_launch() {
  python3 -c "import json,sys; sys.exit(0 if json.load(open('$RD/registration/record_B_conditions_receipt_E6n.json')).get('all_pass') else 1)" \
    || { log "生效条件未全过：不启动后段"; exit 2; }
  : > "$RD/logs/post_acc.pids"; : > "$RD/logs/post_rand.pids"; : > "$RD/logs/post_aux.pids"
  for s in 2019-2023 2024-2026; do
    for f in $FORMS8; do [ -f "$RD/accounts/$s/$f.npz" ] || bg "acc_${s}_${f}" "$RD/logs/post_acc.pids" python3 e6n_accounts.py --seg "$s" --parent "$f"; done
    for f in $FORMS6; do [ -f "$RD/accounts_support/$s/$f.npz" ] || bg "sup_${s}_${f}" "$RD/logs/post_acc.pids" python3 e6n_support.py --seg "$s" --form "$f"; done
  done
  bg rand_2019-2023_p0_1024 "$RD/logs/post_rand.pids" python3 e6n_rand.py run --seg 2019-2023 --workers 58 --claim
  bg rand_2024-2026_p0_1024 "$RD/logs/post_rand.pids" python3 e6n_rand.py run --seg 2024-2026 --workers 28 --claim
  local P19 P24
  P19=$(sed -n 1p "$RD/logs/post_rand.pids"); P24=$(sed -n 2p "$RD/logs/post_rand.pids")
  log "后段账户 / 支持 / 随机已启动（随机父进程 $P19 / $P24）"
  waitfile "$RD/logs/post_acc.pids"
  local miss=0
  for s in 2019-2023 2024-2026; do
    for f in $FORMS8; do [ -f "$RD/accounts/$s/$f.npz" ] || { log "缺账户 $s $f"; miss=1; }; done
    for f in $FORMS6; do [ -f "$RD/accounts_support/$s/$f.npz" ] || { log "缺支持桥 $s $f"; miss=1; }; done
  done
  [ $miss -eq 0 ] || { log "FAIL 后段账户 / 支持未齐（随机继续在跑）"; exit 1; }
  log "后段账户 / 支持完成"
  for s in 2019-2023 2024-2026; do
    for f in $FORMS6; do bg "b2run_${s}_${f}" "$RD/logs/post_aux.pids" python3 e6n_b2_run.py --seg "$s" --forms "$f"; done
    bg "b3_$s" "$RD/logs/post_aux.pids" python3 e6n_b3.py --seg "$s"
    bg "b4_$s" "$RD/logs/post_aux.pids" python3 e6n_b4.py --seg "$s"
    for t in fourway cdose mchm; do bg "decomp_${t}_$s" "$RD/logs/post_aux.pids" python3 e6n_decomp.py "$t" --seg "$s"; done
  done
  log "后段 B2 / B3 / B4 / 分解已启动"
  waitpids "$P24"
  if kill -0 "$P19" 2>/dev/null; then
    local total claimed
    total=$(python3 -c "
import pandas as pd
M = pd.read_csv('$RD/registry/random_manifest_E6n.csv', keep_default_na=False)
print(M.groupby(['mechanism', 'group']).ngroups * 8)")
    claimed=$(ls "$RD/randoms_claims/2019-2023" 2>/dev/null | wc -l)
    log "均衡：2024-2026 随机已完；2019-2023 已认领 $claimed / $total"
    if [ $((total - claimed)) -ge 28 ]; then
      bg rand_2019-2023_p0_1024_b "$RD/logs/post_rand.pids" python3 e6n_rand.py run --seg 2019-2023 --workers 28 --claim
    fi
  fi
  log "STAGE_DONE post_launch"
}

stage_post_close() {
  log "等后段随机父进程 $(tr '\n' ' ' < "$RD/logs/post_rand.pids")"
  waitfile "$RD/logs/post_rand.pids"
  grep -h "ALL_DONE\|FAILED" "$RD"/logs/rand_2019-2023_p0_1024*.log "$RD"/logs/rand_2024-2026_p0_1024*.log | cut -c1-300 >> "$LOG"
  for s in 2019-2023 2024-2026; do
    local m
    m=$(python3 e6n_seal.py missing "$s")
    if [ "${m:-1}" != "0" ]; then
      log "补跑 $s 首 1,024 缺回执分片 $m 个（非认领单父进程，只跑缺的）"
      run python3 e6n_rand.py run --seg "$s" --workers 60
    fi
  done
  for s in 2019-2023 2024-2026; do
    run python3 e6n_stats.py desc --seg "$s" --out results/full
    run python3 e6n_stats.py cmp --seg "$s" --out results/full
  done
  topup_loop results/full 90 2019-2023 2024-2026
  for s in 2010-2014 2015-2018; do
    for f in descriptor_stats comparison_stats random_refs mc_plan; do cp -p "$RD/results/deriv/${f}_$s.csv" "$RD/results/full/${f}_$s.csv" || { log "FAIL 拷推导段 $f $s"; exit 1; }; done
  done
  run python3 e6n_seal.py seal post
  run python3 e6n_stats.py full --out results/full
  run python3 e6n_policy.py
  run python3 e6n_bootstrap.py
  log "STAGE_DONE post_close"
}

stage_finish() {
  log "等 B2 / B3 / B4 / 分解 / 补齐表"
  while pgrep -f "e6n_(b2_run|b3|b4|decomp|fixed)\.py" > /dev/null; do sleep 60; done
  for s in 2010-2014 2015-2018 2019-2023 2024-2026; do
    [ -f "$RD/results/full/penalty/penalty_change_$s.csv" ] || run python3 e6n_fixed.py penalty --seg "$s"
  done
  [ -f "$RD/results/full/measurement_raw_ledger.csv" ] || run python3 e6n_fixed.py rawledger
  run python3 e6n_b56.py b5
  run python3 e6n_b56.py b6
  run python3 e6n_deliver.py consolidate
  run python3 e6n_queries.py run --phase full
  run python3 e6n_fixed.py all_post
  run python3 e6n_reports.py all
  run python3 e6n_notes.py
  run python3 e6n_deliver.py schema
  run python3 e6n_deliver.py register
  run python3 e6n_deliver.py replica
  run python3 e6n_closure.py
  log "PIPELINE_DONE"
}

case "${1:-}" in
  wait_deriv) stage_wait_deriv "${2:?缺 deriv_close 链 PID}"; stage_post_launch; stage_post_close; stage_finish ;;
  post_launch) stage_post_launch; stage_post_close; stage_finish ;;
  post_close) stage_post_close; stage_finish ;;
  finish) stage_finish ;;
  *) echo "用法：$0 wait_deriv <链 PID> | post_launch | post_close | finish"; exit 2 ;;
esac
