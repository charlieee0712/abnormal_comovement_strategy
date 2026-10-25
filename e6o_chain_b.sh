#!/bin/bash
# E6o B 链（后段；只在 seal_A2 之后）：账户 B（A2_end 续跑）→ 影子 B → 随机 B（全部机制 128 路径）→ 主母体精度增补（1,024）→ 推导段重放核对
#   → 统计 → 随机汇总 / 政策 / 72 → 诊断 D-1…D-6 → Stage 0 终版引擎刷新 → 恒等合并 → 声明 / 账本结果栏 → 报告 → 读法注 / 登记
#   → registry 状态 → SCHEMA → seal_final → 副本包 + 交付目录 → 决策端脚本 → 闭包门 → 交付目录定稿
# 用法：bash e6o_chain_b.sh [起始步名]（从某步续跑；默认从头）
set -u
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261017_2138_E6o_account_exit_stage" && pwd)
export E6O_WORK=$W OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MKL_NUM_THREADS=2 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR=$W/tmp/numba_cache
cd "$C"
PIN="taskset -c 96-191,288-383"
FROM="${1:-}"
GO=0
[ -z "$FROM" ] && GO=1
step() {
  local n=$1; shift
  if [ $GO -eq 0 ]; then [ "$n" = "$FROM" ] && GO=1 || { echo "skip $n"; return 0; }; fi
  echo "[$(date '+%F %T')] $n start"
  $PIN "$@" > "$W/logs/$n.log" 2>&1 || { echo "[$(date '+%F %T')] $n FAILED"; exit 1; }
  echo "[$(date '+%F %T')] $n ok"
}
[ -f "$W/registration/seal_A2.json" ] || { echo "seal_A2 missing"; exit 1; }
step accounts_B    python3 e6o_run.py accounts --phase B --workers 64
step shadow_B      python3 e6o_run.py shadow --phase B --workers 12
step randoms_B     python3 e6o_run.py randoms --phase B --workers 96 --batch 16
step topup_B       python3 e6o_topup.py --workers 96
step replaycheck   python3 e6o_replaycheck.py
step stats_B       python3 e6o_stats.py --phase B
step policy_B      python3 e6o_policy.py --phase B
step diag          python3 e6o_diag.py
step s0f_pre       python3 e6o_stage0_final.py pre
step stage0_final  python3 e6o_stage0.py --workers 64
step stage0b_final python3 e6o_stage0b.py
step s0f_post      python3 e6o_stage0_final.py post
step identities    python3 e6o_closure.py identities
step claims        python3 e6o_claims.py
step reports       python3 e6o_reports.py
step notes         python3 e6o_notes.py
step registry      python3 e6o_closure.py registry
step schema        python3 e6o_closure.py schema
step seal_final    python3 e6o_seal.py final
step handoff       python3 e6o_closure.py handoff
step dscript       python3 e6o_closure.py dscript
step gate          python3 e6o_closure.py gate final
step finalize      python3 e6o_closure.py finalize
echo "chain_b done $(date '+%F %T')"
