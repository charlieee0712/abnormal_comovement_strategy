#!/bin/bash
# E6k 封存之后的分析链。用法：
#   e6k_chain_analysis.sh deriv   —— seal_deriv 之后：推导两段诊断（HG 连续、影子、机制、风险、对照分布）
#   e6k_chain_analysis.sh full    —— seal_post 之后：四段统计 → 政策 → bootstrap → 两后段诊断 → HG 接续 → 衰减 → 报告 → 机器表
set -u
cd /mnt/sda2/lichenchen/code/project_core
R=/mnt/sda2/lichenchen/results/20260928_2325_E6k_k_binding_stage
L=$R/logs/chain_analysis_$1.log
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
run() { echo "$(date '+%F %T') START $*" >> $L; taskset -c 96-191,288-383 python3 "$@" >> $L 2>&1; rc=$?; echo "$(date '+%F %T') END rc=$rc $*" >> $L; return $rc; }
if [ "$1" = deriv ]; then
  run e6k_hg_continuous.py --segments 2010-2014,2015-2018 &
  for s in 2010-2014 2015-2018; do run e6k_shadow.py --segment $s & run e6k_mechanisms.py --segment $s & run e6k_risk.py --segment $s & run e6k_control_dist.py --segment $s & done
  wait
  echo "ANALYSIS_DERIV_DONE $(date +%F_%T)" >> $L
  exit 0
fi
for s in 2010-2014 2015-2018 2019-2023 2024-2026; do run e6k_stats.py --segment $s --phase full & done
wait
run e6k_policy.py
run e6k_bootstrap.py &
run e6k_hg_continuous.py --segments 2019-2023,2024-2026 --init-from 2015-2018 &
run e6k_decay.py &
for s in 2019-2023 2024-2026; do run e6k_shadow.py --segment $s & run e6k_mechanisms.py --segment $s & run e6k_risk.py --segment $s & run e6k_control_dist.py --segment $s & done
wait
for r in e6k_report_r0.py e6k_report_part2.py e6k_report_part3.py e6k_report_mechanisms.py e6k_report_carried.py; do run $r; done
run e6k_deliver.py --tables
run e6k_report_cards.py
echo "ANALYSIS_FULL_DONE $(date +%F_%T)" >> $L
