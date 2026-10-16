# -*- coding: utf-8 -*-
"""E6m 阶段 N · N2：plan §16 内嵌脚本（e6m_spec_tests.py，sha 25020c82…，不改断言）在云机 factor 环境实跑。
产物 stage0/plan_tests/：test_results.txt、registry.json、primary.json、supplemental.json、comparison.json、env.json、
plan_tests_status.csv（131 项逐条）、raw_<attempt>/（脚本原样输出）与 sha 清单。每次 attempt 保留，不覆盖。"""
import os
import sys
import json
import time
import shutil
import argparse
import subprocess
import importlib.util

import e6m_core as M

HANDOFF = os.path.join(M.RUNS, 'handoff', 'E6m')
SPEC_SHA = '25020c8239adb9b7a2ee86a45aa653005689b38127d94187a1be546fe062cca9'
EXPECT = dict(main_descriptors=26232, primary=72, mandatory_v11_addenda=384, compiled_base_comparisons=43428, tests=131)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', default='a1')
    a = ap.parse_args()
    D = M.P('stage0', 'plan_tests')
    os.makedirs(D, exist_ok=True)
    spec = os.path.join(D, 'e6m_spec_tests.py')
    if not os.path.exists(spec):
        shutil.copyfile(os.path.join(HANDOFF, 'e6m_spec_tests.py'), spec)
    if M.sha_file(spec) != SPEC_SHA:
        raise RuntimeError('spec 脚本 sha 不符')
    raw = os.path.join(D, 'raw_%s' % a.attempt)
    if os.path.exists(raw):
        raise RuntimeError('attempt 目录已存在（每次 attempt 保留，不覆盖）：%s' % raw)
    t0 = time.time()
    pr = subprocess.run([sys.executable, spec, raw], capture_output=True, text=True, cwd=D)
    wall = time.time() - t0
    txt = 'returncode=%d wall_s=%.2f\n--- stdout ---\n%s\n--- stderr ---\n%s\n' % (pr.returncode, wall, pr.stdout, pr.stderr)
    M.atomic_write_text(os.path.join(D, 'test_results_%s.txt' % a.attempt), M.san(txt))
    res = json.load(open(os.path.join(raw, 'results.json'), encoding='utf-8'))
    st = M.pd.DataFrame(res['tests'])
    st.insert(0, 'attempt', a.attempt)
    st['note'] = ''
    M.atomic_write_csv(os.path.join(D, 'plan_tests_status_%s.csv' % a.attempt), st)
    # 规范名产物（附录 N2）：registry / supplemental / comparison 原样复制；primary 由同一模块的 primary() 导出
    sp = importlib.util.spec_from_file_location('e6m_spec_tests_ref', spec)
    mod = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(mod)
    prim = [dict(zip(('measurement', 'parent', 'operator', 'param', 'alpha', 'memory', 'H', 'adapter', 'condition'), t)) for t in mod.primary()]
    shutil.copyfile(os.path.join(raw, 'registry.json'), os.path.join(D, 'registry.json'))
    shutil.copyfile(os.path.join(raw, 'v11_addenda.json'), os.path.join(D, 'supplemental.json'))
    shutil.copyfile(os.path.join(raw, 'base_comparisons.json'), os.path.join(D, 'comparison.json'))
    M.atomic_write_json(os.path.join(D, 'primary.json'), prim)
    env = dict(M.env_versions(), spec_reported_python=res['python'], spec_reported_numpy=res['numpy'], spec_script_sha256=res['script_sha256'],
               returncode=pr.returncode, wall_s=round(wall, 2), attempt=a.attempt, run_at=time.strftime('%Y-%m-%d %H:%M:%S'), machine=M.MACHINE)
    M.atomic_write_json(os.path.join(D, 'env.json'), env)
    got = dict(main_descriptors=res['main_descriptors'], primary=len(prim), mandatory_v11_addenda=res['mandatory_v11_addenda'],
               compiled_base_comparisons=res['compiled_base_comparisons'], tests=res['run'])
    chk = [dict(item=k, expected=v, got=got[k], status='PASS' if got[k] == v else 'FAIL') for k, v in EXPECT.items()]
    chk.append(dict(item='passed', expected=EXPECT['tests'], got=res['passed'], status='PASS' if res['passed'] == EXPECT['tests'] else 'FAIL'))
    chk.append(dict(item='script_sha256', expected=SPEC_SHA, got=res['script_sha256'], status='PASS' if res['script_sha256'] == SPEC_SHA else 'FAIL'))
    chk.append(dict(item='blocks', expected='见 plan §10.2', got=json.dumps(res['blocks'], sort_keys=True), status='INFO'))
    M.atomic_write_csv(os.path.join(D, 'plan_tests_counts_%s.csv' % a.attempt), M.pd.DataFrame(chk))
    files = sorted(os.listdir(D)) + ['%s/%s' % (os.path.basename(raw), f) for f in sorted(os.listdir(raw))]
    man = [dict(file=f, sha256=M.sha_file(os.path.join(D, f)), bytes=os.path.getsize(os.path.join(D, f))) for f in files
           if os.path.isfile(os.path.join(D, f)) and not f.startswith('sha256_manifest')]
    M.atomic_write_csv(os.path.join(D, 'sha256_manifest_%s.csv' % a.attempt), M.pd.DataFrame(man))
    ok = pr.returncode == 0 and all(r['status'] in ('PASS', 'INFO') for r in chk)
    M.write_receipt('stage0_N2_plan_tests_%s' % a.attempt, [os.path.join(D, f) for f in ('registry.json', 'primary.json', 'supplemental.json',
                                                                                         'comparison.json', 'env.json')],
                    status='SUCCEEDED' if ok else 'FAILED', inputs=[spec], code=[__file__, M.__file__], counts=got, passed=res['passed'])
    print(json.dumps(dict(got, passed=res['passed'], returncode=pr.returncode, wall_s=round(wall, 2)), ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
