#!/bin/sh
# E6j 执行端等待链（封存之后的计算，不生成报告；报告由执行端核对输入后手动生成）：
#  P：等 e6j_chain_p_post.sh 写 "chain done"（任一步 "-> stop" 则本段放弃）→ e6j_policy_p.py（正式，核封存）→ e6j_policy_extra.py
#  B：等 B 随机链（PID 354272）结束 → 推导段 stats_b final（2 进程）→ 封存 B_post v1 → 后段 stats_b final（2 进程）
#     → 主配置 IID MCSE 检查（> .03 则停，交执行端排增补）→ e6j_bands_b.py
# C1 carried 链在 354272 结束时以 -P 16 自启；本链同时最多 2 个进程，合计 ≤ 24。
R=/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot
C=/mnt/sda2/lichenchen/code/project_core
L=$R/logs/chain_reads.log
ulimit -u 4096
cd $C || exit 1
echo "start $(date '+%F %T') pid $$" >> $L
T="taskset -c 96-191,288-383"
# ---------------- P
while ! grep -qE "chain done|-> stop" $R/logs/chain_p_post.log 2>/dev/null; do sleep 60; done
if grep -q "chain done" $R/logs/chain_p_post.log; then
  $T python3 -B e6j_policy_p.py >> $L 2>&1 && echo "policy_p ok $(date '+%F %T')" >> $L && \
  $T python3 -B e6j_policy_extra.py >> $L 2>&1 && echo "policy_extra ok $(date '+%F %T')" >> $L || echo "P reads failed $(date '+%F %T')" >> $L
else
  echo "P post chain stopped; P reads skipped $(date '+%F %T')" >> $L
fi
# ---------------- B
while kill -0 354272 2>/dev/null; do sleep 60; done
echo "B rand chain gone $(date '+%F %T')" >> $L
$T python3 -B e6j_stats_b.py --segment 2010-2014 --tag final >> $L 2>&1 &
P1=$!
$T python3 -B e6j_stats_b.py --segment 2015-2018 --tag final >> $L 2>&1 &
P2=$!
wait $P1; E1=$?; wait $P2; E2=$?
echo "stats_b deriv final exit $E1 $E2 $(date '+%F %T')" >> $L
python3 -B e6j_seal.py --package B_post >> $L 2>&1 || { echo "seal B_post v1 not ok -> stop $(date '+%F %T')" >> $L; exit 2; }
$T python3 -B e6j_stats_b.py --segment 2019-2023 --tag final >> $L 2>&1 &
P1=$!
$T python3 -B e6j_stats_b.py --segment 2024-2026 --tag final >> $L 2>&1 &
P2=$!
wait $P1; E1=$?; wait $P2; E2=$?
echo "stats_b post final exit $E1 $E2 $(date '+%F %T')" >> $L
python3 -B - >> $L 2>&1 <<'EOF'
import pandas as pd, glob, sys
R = '/mnt/sda2/lichenchen/results/20260927_0038_E6j_k_two_dimension_pilot'
over = []
for p in sorted(glob.glob(R + '/results_B/descriptor_stats_*_final.csv')):
    x = pd.read_csv(p, usecols=lambda c: c in ('segment', 'mother', 'block', 'alpha', 'H', 'mcse_IID'))
    m = x[(x.alpha == 0.25) & (x.H == 5)]
    g = m.groupby(['segment', 'mother', 'block']).mcse_IID.max()
    over += [k for k, v in g.items() if v > 0.03]
print('B main-config IID MCSE > .03 groups:', len(over), over[:10])
sys.exit(3 if over else 0)
EOF
if [ $? -ne 0 ]; then echo "B MC topup needed -> stop $(date '+%F %T')" >> $L; exit 3; fi
$T python3 -B e6j_bands_b.py >> $L 2>&1 && echo "bands_b ok $(date '+%F %T')" >> $L || echo "bands_b failed $(date '+%F %T')" >> $L
echo "chain done $(date '+%F %T')" >> $L
