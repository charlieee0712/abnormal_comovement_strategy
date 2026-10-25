#!/bin/bash
# E6q S0-J（合同脚本 205 项 + 七指纹 → verify/spec、registration/spec）与 S0-K（D 脚本 sha → py_compile → 夹具空跑）。用法：bash e6q_s0jk.sh
set -u
C=$(cd "$(dirname "$0")" && pwd)
W=$(cd "$C/../../results/20261023_0040_E6q_sell_reinvest_split" && pwd)
cd "$W"
PY=python3
# ---- S0-J
mkdir -p verify/spec registration/spec tmp/s0j
cp inputs/e6q_contract.py tmp/s0j/e6q_contract.py
echo "contract_sha256 $(sha256sum tmp/s0j/e6q_contract.py | cut -c1-64)" > tmp/s0j/sha_check.txt
( cd tmp/s0j && PYTHONDONTWRITEBYTECODE=1 $PY -W error e6q_contract.py --out e6q_contract_out ) > verify/spec/spec_run.txt 2>&1
echo "rc=$?" >> verify/spec/spec_run.txt
$PY --version >> verify/spec/spec_run.txt 2>&1
cp tmp/s0j/e6q_contract_out/verification.txt verify/spec/verification.txt
( cd tmp/s0j/e6q_contract_out && sha256sum *.json cc_statement_carry.csv ) > verify/spec/SHA256.txt
mkdir -p verify/spec/e6q_contract_out
cp tmp/s0j/e6q_contract_out/* verify/spec/e6q_contract_out/
cp tmp/s0j/e6q_contract_out/*.json tmp/s0j/e6q_contract_out/cc_statement_carry.csv registration/spec/
$PY - <<'EOF'
import json
v = json.load(open('verify/spec/verification.txt'))
exp = {'registry.json': '58dff4fc', 'comparisons.json': '528112f8', 'compound.json': '9e788459', 'random_refs.json': 'cd481c6a',
       'feedback_refs.json': 'f61b4009', 'primary.json': 'f6c7e0e0', 'claims.json': '641187b4'}
ok = all(v['json_sha256'][k].startswith(x) for k, x in exp.items())
print('S0-J test_count', v['test_count'], 'fingerprints_ok', ok, 'counts', json.dumps(v['counts']))
EOF
# ---- S0-K
mkdir -p verify/decision tmp/s0k
cp inputs/E6q_D_stage2.py verify/decision/E6q_D_stage2.py
echo "d_script_sha256 $(sha256sum verify/decision/E6q_D_stage2.py | cut -c1-64)"
PYTHONPYCACHEPREFIX=$W/tmp/s0k/pyc $PY -m py_compile verify/decision/E6q_D_stage2.py && echo "py_compile OK"
rm -rf tmp/s0k/fixture
PYTHONDONTWRITEBYTECODE=1 $PY verify/decision/E6q_D_stage2.py --make-fixture tmp/s0k/fixture --spec-dir verify/spec/e6q_contract_out > tmp/s0k/make_fixture.log 2>&1
echo "make_fixture rc=$?"
PYTHONDONTWRITEBYTECODE=1 $PY verify/decision/E6q_D_stage2.py --root tmp/s0k/fixture --out tmp/s0k/fixture/out > tmp/s0k/run_fixture.log 2>&1
echo "run_fixture rc=$?"
ls tmp/s0k/fixture/out
$PY - <<'EOF'
import csv, collections, glob
fs = glob.glob('tmp/s0k/fixture/out/*probes*.csv')
rows = list(csv.DictReader(open(fs[0], encoding='utf-8'))) if fs else []
print('S0-K probes', len(rows), dict(collections.Counter(r.get('status') for r in rows)))
for r in rows:
    if r.get('status') not in ('PASS',):
        print(' ', r.get('probe_id'), r.get('status'), (r.get('detail') or '')[:160])
EOF
tail -3 tmp/s0k/run_fixture.log | cut -c1-300
