#!/usr/bin/env bash
# E6m 阶段 S · S1–S3 运行手册（brief §5 S1–S3；X01 + P3 锚文件到云机，或 47 恢复后）。
# 用法：bash e6m_s_runbook.sh s1|s2|s3|s4|s5a|s5b|all   任一步非 0 即停；任务级断点续跑由回执保证（e6m_s_queue 跳过已 SUCCEEDED 的任务）。
# 方式 B（用户 2026-10-05 原话"B 继续推进"，registration/authorization_status_E6m_S.json）：s2 冻结时照录写 record_B_preauthorized，s3 后不停，all = s1 → s5a；执行端读结果写 notes 后 s5b 交付。
# 顺序：S1 Stage 0 S（源锚 / 真实数据恒等 / 随机复现 / P44）→ S2 名单 / 附属 / Stage A（真实结构，四段掩码层事实）→ A2-7 → Stage 0 门 → A1-auto → Stage B 冻结
#      → S3 推导两段账户 / 随机 / MC 增补 → seal_deriv → 推导段统计 / MDE / query / part1 → 生效条件回执 → 记录 B 草稿 → 方式 A：停等用户一句话。
# 不在本脚本里：用户授权记录（e6m_s_stage_b.py approve 只照录用户原话）、两后段（S4 另一份手册，post_gate 拦）。
set -euo pipefail
if [ -f /root/miniconda3/etc/profile.d/conda.sh ]; then source /root/miniconda3/etc/profile.d/conda.sh && conda activate factor; fi   # 云机；47 用登录环境的 python
C=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd); cd "$C"   # 脚本所在的 project_core（47 的 /mnt/sda2 下有多人目录，不能取 ls 第一个）
: "${E6M_WORK:?E6M_WORK 未设}"
export E6M_STAGE=S OMP_NUM_THREADS=${OMP_NUM_THREADS:-4} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-4} MKL_NUM_THREADS=${MKL_NUM_THREADS:-4}
W=$E6M_WORK
PIN=(); if [ -n "${E6M_TASKSET:-}" ]; then PIN=(taskset -c "$E6M_TASKSET"); fi   # 47 跑批绑核（设 E6M_TASKSET）；云机不设 = 不绑
DERIV="2010-2014 2015-2018"
ALL="2010-2014 2015-2018 2019-2023 2024-2026"
step() { local name=$1; shift; echo "== [$(date '+%F %T')] $name：$*"; E6M_TASK="S_rb_$name" ${PIN[@]+"${PIN[@]}"} "$@"; }
par_segs() {   # 四段并行（每段一个进程，--seg 由本函数补）；全部结束后任一段非 0 即停（日志 logs/rb_<名>_<段>.log）
  local name=$1; shift
  local pids=() s p rc=0
  mkdir -p "$W/logs"
  for s in $ALL; do
    echo "== [$(date '+%F %T')] ${name}_$s（并行）：$* --seg $s"
    ( E6M_TASK="S_rb_${name}_$s" ${PIN[@]+"${PIN[@]}"} "$@" --seg "$s" 2>&1 | sed -u -E 's#/home/[^/[:space:]]+#<HOME>#g; s#envs/[^/[:space:]]+#envs/<ENV>#g' > "$W/logs/rb_${name}_$s.log" ) &
    pids+=($!)
  done
  for p in "${pids[@]}"; do wait "$p" || rc=1; done
  [ $rc -eq 0 ] || { echo "== ${name}：有段失败（见 logs/rb_${name}_*.log）"; exit 1; }
}

s1() {
  step s0_imports python e6m_stage0_S_engine.py imports          # 先刷新账户侧 import 检查（X01 到位的冒烟；旧表会让 close 一直 SOURCE_WAIT）
  step s0_intake python e6m_stage0_S.py intake
  step s0_identity python e6m_stage0_S.py identity
  step s0_features python e6m_stage0_S_feat.py features
  step s0_anchormap python e6m_stage0_S_feat.py anchormap
  step s0_claims python e6m_stage0_S_feat.py claims
  for s in $ALL; do step "s0_structid_$s" python e6m_stage0_S_engine.py structid --seg "$s"; done
  step s0_p44_real python e6m_stage0_S_feat.py p44 --struct real
  for s in $ALL; do step "s0_engine_$s" python e6m_stage0_S_engine.py engine --seg "$s"; done   # 父 / Q0 NATIVE / E6k·E6l 同构 = 已暴露源对象，四段都锚
  step s0_random python e6m_stage0_S_engine.py random --workers 6
}

s2() {
  python e6m_s_queue.py masks
  python e6m_s_queue.py aux
  python e6m_s_queue.py stage_a
  python e6m_s_queue.py memage
  step s0_maskfacts python e6m_stage0_S_feat.py maskfacts --stage-a-dir "$W/stage_a"
  step s0_close python e6m_stage0_S.py close
  step a1_auto python e6m_s_a1auto.py
  step preflight_13b python e6m_s_preflight.py --only 13b               # ⑬b 决策端文件不齐就不冻结（冻结只写一次，冻结后补写进不了卡片 t09）
  step stage_b python e6m_s_stage_b.py stage-b --real
  step stage_b_freeze python e6m_s_stage_b.py freeze --real
}

s3() {
  python e6m_s_queue.py accounts --segs 2010-2014,2015-2018
  python e6m_s_queue.py randoms --segs 2010-2014,2015-2018
  python e6m_s_queue.py topup --segs 2010-2014,2015-2018
  step seal_deriv python e6m_s_seal.py seal deriv
  for s in $DERIV; do
    step "stats_desc_$s" python e6m_s_stats.py desc --acc "$W/accounts" --seg "$s" --out "$W/results/deriv"
    step "stats_cmp_$s" python e6m_s_stats.py cmp --acc "$W/accounts" --seg "$s" --out "$W/results/deriv"
    step "stats_rand_$s" python e6m_s_stats.py rand --acc "$W/accounts" --rand-dir "$W/randoms" --seg "$s" --out "$W/results/deriv"
  done
  step mde80_deriv python e6m_s_mde.py --stats "$W/results/deriv" --cards "$W/registry/cards_stageB_E6m.csv" --out "$W/results/deriv"
  step queries_deriv python e6m_s_queries.py --phase deriv --stats "$W/results/deriv" --stage-a "$W/stage_a" --out "$W/reports/queries_deriv"
  step part1 python e6m_s_part1.py part1 --stats "$W/results/deriv"
  step conditions python e6m_s_stage_b.py conditions
  step record_b_draft python e6m_s_part1.py record-b
  if [ -f "$W/registration/record_B_preauthorized_E6m.json" ]; then
    echo "== 方式 B（事前整表授权，冻结时已照录原话）：推导两段完成并封存；接 s4（post_gate 逐步核授权绑定的清单 sha 与生效条件回执）"
  else
    echo "== 方式 A：推导两段完成并封存。停等用户对两后段的一句话授权；收到后：python e6m_s_stage_b.py approve --mode A --quote '<用户原话>' --date YYYY-MM-DD"
  fi
}

s4() {   # 两后段（post_gate 拦：方式 A 需 approve 原话 + conditions 回执；方式 B 需事前授权）→ 全段统计 / 政策 / 分解 / B3–B6 / 报告
  python e6m_s_queue.py accounts --segs 2019-2023,2024-2026
  python e6m_s_queue.py randoms --segs 2019-2023,2024-2026
  python e6m_s_queue.py topup --segs 2019-2023,2024-2026
  step seal_post python e6m_s_seal.py seal post
  F="$W/results/full"
  for s in $ALL; do
    step "statsF_desc_$s" python e6m_s_stats.py desc --acc "$W/accounts" --seg "$s" --out "$F"
    step "statsF_cmp_$s" python e6m_s_stats.py cmp --acc "$W/accounts" --seg "$s" --out "$F"
    step "statsF_rand_$s" python e6m_s_stats.py rand --acc "$W/accounts" --rand-dir "$W/randoms" --seg "$s" --out "$F"
    for t in fourway capdec trefit weightchange; do step "decomp_${t}_$s" python e6m_s_decomp.py $t --acc "$W/accounts" --seg "$s" --out "$F/decomp"; done
    step "b5_budget_$s" python e6m_b5.py budget --acc "$W/accounts" --stats "$F" --seg "$s" --out "$F/b5"
    step "b5_ledger_$s" python e6m_b5.py ledger --seg "$s" --out "$F/b5"
    step "b5_clock_$s" python e6m_b5.py clock --seg "$s" --out "$F/b5"          # state_clock_ledger（E6l 三时钟移植，L-S5）
    step "b6_$s" python e6m_b6_accounts.py run --seg "$s" --out "$F/b6"
  done
  step statsF_full python e6m_s_stats.py full --out "$F"
  step policy python e6m_s_policy.py --stats "$F" --randoms "$F" --out "$F"
  step bootstrap python e6m_s_bootstrap.py --acc "$W/accounts" --out "$F/bootstrap"
  for t in event symdec sig4; do step "b4_$t" python e6m_b4.py $t --acc "$W/accounts" --out "$F/b4"; done
  par_segs b4sig13 python e6m_b4_sig.py run --only sig1,sig3 --out "$F/b4"     # B4 签名 1 / 3（引擎层；签名 1 账户锚先落地；L-S3）
  par_segs b4sig2 python e6m_b4_sig.py run --only sig2 --out "$F/b4"           # 签名 2 单独一步（每段约 40 分钟，四段并行；数据形状意外不挡签名 1 / 3）
  step b3_anchor python e6m_b3_merge.py anchor
  s4_tail
}

s4_tail() {   # s4 自 b3_tables 起的后半（10-12 补丁十五建，用于锚 ii 修后续跑；补丁十六起点前移到 b3_tables：B3 表要重建）；不重跑增补 / 封存；整段 s4 仍按原顺序调用，行为不变
  F="$W/results/full"
  step b3_tables python e6m_b3_merge.py tables --out "$W/reports/b3"
  step cont_masks python e6m_s_continuous.py masks --struct real        # 附属第 7 项源理论连续链：名单层（四段按序；锚 i）
  step cont_ledger python e6m_s_continuous.py ledger --struct real      # 账户层（封存核对 + 后段守卫；锚 ii 不过即停）
  step aux_status python e6m_s_aux_status.py --phase full --out "$F/aux_status"
  step queries_full python e6m_s_queries.py --phase full --stats "$F" --stage-a "$W/stage_a" --policy "$F/policy_E6m.csv" --out "$W/reports/queries_full"
  step fixed_full python e6m_s_fixed.py --phase full --stats "$F" --stage-a "$W/stage_a" --decomp "$F/decomp" --policy "$F/policy_E6m.csv" --b4 "$F/b4" --b5 "$F/b5" \
       --b6 "$F/b6" --b3 "$W/reports/b3" --aux "$F/aux_status" --masks "$W/masks" --out "$W/reports/fixed_full"
  step reports python e6m_s_reports.py all --stats "$F" --policy "$F/policy_E6m.csv" --decomp "$F/decomp" --b4 "$F/b4" --b5 "$F/b5" --b6 "$F/b6" --b3 "$W/reports/b3" \
       --aux "$F/aux_status" --queries "$W/reports/queries_full" --cont "$F/continuous" --fixed "$W/reports/fixed_full"
}

supp1() {   # 补充件 S1（2026-10-12 用户定"现在补算成补充件"，补丁十九）：附属 item 6 SAME_N_CORE_DEEP × SUPP V_ALL_KNOWN 240 行；写 supp/S1/，不改封存件
  par_segs supp1 python e6m_s_supp1.py run
  step supp1_manifest python e6m_s_supp1.py manifest
}

s5a() {  # 交付文档：代码登记重生成 → 限制登记 / 经验 / 代码登记三份进 reports/（brief §9）；之后停，执行端读结果写 notes
  step code_register python e6m_s_code_register.py
  step deliver_docs python e6m_s_deliver.py docs
  echo "== 执行端读结果，按骨架 stageN/REVIEW_input_notes_skeleton.md 写 reports/E6m_REVIEW_input_notes.md（数字用 e6m_s_deliver.pick 从机器表取），再跑 s5b"
}

s5b() {  # notes 在 → 副本包（含 notes）→ 交付索引 → 闭包门 → 复制到 handoff
  step notes_check python e6m_s_deliver.py notes-check
  step replica_final python e6m_s_replica.py --stage final
  step review_input python e6m_s_deliver.py review
  step closure_gate python e6m_s_gate_close.py
  step deliver_copy python e6m_s_deliver.py copy
}

case "${1:-}" in
  s1) s1 ;;
  s2) s2 ;;
  s3) s3 ;;
  s4) s4 ;;
  s4tail) s4_tail ;;
  supp1) supp1 ;;
  s5a) s5a ;;
  s5b) s5b ;;
  all)                                                                   # 方式 B 一口气：s1 → s5a（任一步非 0 即停；后段由 post_gate 逐步拦）；notes 写完再 s5b
    step preflight python e6m_s_preflight.py                             # 先查外部输入 / ⑬b / 方式 B，缺一项就不开跑（免得算一天才在后段守卫处停）
    s1; s2
    [ -f "$W/registration/record_B_preauthorized_E6m.json" ] || { echo "冻结后未见 record_B_preauthorized_E6m.json：停"; exit 3; }
    s3; s4; s5a ;;
  *) echo "用法：$0 s1|s2|s3|s4|s5a|s5b|all"; exit 2 ;;
esac
