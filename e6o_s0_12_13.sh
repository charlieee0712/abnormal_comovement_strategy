#!/bin/bash
# E6o S0-12（决策端脚本：核 sha → py_compile → 合同夹具空跑）与 S0-13（spec tests 隔离目录 -W error 重跑 + 四表 sha）。
# 用法：bash e6o_s0_12_13.sh <E6o 结果目录>
set -u
W="$1"
CODE="$(cd "$(dirname "$0")" && pwd)"
cd "$W" || exit 2
LOG="$W/logs/s0_12_13.log"
: > "$LOG"
echo "[S0-12] $(date '+%F %T')" | tee -a "$LOG"
mkdir -p verify/decision
cp -p inputs/E6o_D_stage2.py verify/decision/E6o_D_stage2.py
D_SHA=$(sha256sum verify/decision/E6o_D_stage2.py | cut -d' ' -f1)
echo "D_SHA=$D_SHA" | tee -a "$LOG"
python3 -m py_compile verify/decision/E6o_D_stage2.py; PC=$?
echo "PY_COMPILE_EXIT=$PC" | tee -a "$LOG"
FX="$W/tmp/s0_12_fixture"
rm -rf "$FX"
python3 "$CODE/e6o_s0_fixture.py" --out "$FX" 2>&1 | tee -a "$LOG"
python3 verify/decision/E6o_D_stage2.py --root "$FX" --handoff "$FX/handoff" --out "$FX/out" > "$FX/run_stdout.txt" 2>&1; RX=$?
echo "FIXTURE_RUN_EXIT=$RX" | tee -a "$LOG"
tail -n 40 "$FX/run_stdout.txt" | cut -c1-260 | tee -a "$LOG"
python3 - "$FX/out/E6o_D_probes_stage2.csv" <<'EOF' 2>&1 | tee -a "$LOG"
import sys, pandas as pd
d = pd.read_csv(sys.argv[1], dtype=str, keep_default_na=False)
ids = ['S%02d' % i for i in range(1, 25)]
miss = [i for i in ids if i not in set(d['S_id'])]
nost = int((d['status'].str.len() == 0).sum())
print('FIXTURE_PROBES rows=%d missing=%s empty_status=%d counts=%s' % (len(d), miss, nost, d['status'].value_counts().to_dict()))
EOF
echo "[S0-13] $(date '+%F %T')" | tee -a "$LOG"
ISO="$W/tmp/s0_13_spec_iso"
rm -rf "$ISO"; mkdir -p "$ISO"
cp -p inputs/e6o_spec_tests.py "$ISO/"
S_SHA=$(sha256sum "$ISO/e6o_spec_tests.py" | cut -d' ' -f1)
echo "SPEC_SHA=$S_SHA" | tee -a "$LOG"
( cd "$ISO" && python3 -I -W error e6o_spec_tests.py --out ./e6o_spec_checks ) > verify/spec/spec_run.txt 2>&1; SX=$?
echo "SPEC_EXIT=$SX" | tee -a "$LOG"
tail -n 6 verify/spec/spec_run.txt | cut -c1-400 | tee -a "$LOG"
mkdir -p verify/spec/e6o_spec_checks
cp -p "$ISO"/e6o_spec_checks/*.json verify/spec/e6o_spec_checks/
( cd verify/spec && sha256sum e6o_spec_checks/registry.json e6o_spec_checks/comparisons.json e6o_spec_checks/parents.json e6o_spec_checks/level_worst_refs.json e6o_spec_checks/test_results.json > SHA256.txt; echo "$S_SHA  e6o_spec_tests.py" >> SHA256.txt )
cat verify/spec/SHA256.txt | tee -a "$LOG"
echo "[done] $(date '+%F %T')" | tee -a "$LOG"
