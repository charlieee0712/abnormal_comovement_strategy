# -*- coding: utf-8 -*-
"""E6m 阶段 N · N4：import 闭包动态核验（brief W15 / A8；附录 N4）。每条闭包在独立子进程里 import，
用 sys.addaudithook 记录 import 期打开的全部文件；数据侧应不含 e6e_core 且 import 期不读数据文件；
账户侧（e6k_env → e6j_engine → e6f_core → e6e_core）预期在云机因 import 期读 E6 宽扫描 roles.csv（X01）失败。
输出 registry/import_closure_E6m.csv 与 registry/import_closure_E6m.json。"""
import os
import sys
import json
import subprocess

import pandas as pd

import e6m_core as M

PROBE = r'''
import sys, os, json
CODE = %(code)r
sys.path.insert(0, CODE)
opened = []
def hook(ev, args):
    if ev == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
        p = os.fsdecode(args[0])
        if not p.endswith(('.py', '.pyc', '.so', '.pth')) and '/lib/python' not in p and 'site-packages' not in p and '__pycache__' not in p:
            opened.append(os.path.realpath(p))
sys.addaudithook(hook)
before = set(sys.modules)
targets = %(targets)r
res = dict(targets=targets, ok=True, error='', failed_at='')
for t in targets:
    try:
        __import__(t)
    except BaseException as e:
        res.update(ok=False, error='%%s: %%s' %% (type(e).__name__, str(e)[:300]), failed_at=t)
        break
mods = []
for m in sorted(set(sys.modules) - before):
    f = getattr(sys.modules.get(m), '__file__', None) or ''
    if f and os.path.realpath(f).startswith(os.path.realpath(CODE) + os.sep):
        mods.append(m)
res['project_modules'] = mods
res['opened_non_code'] = sorted(set(opened))
print('__JSON__' + json.dumps(res))
'''

DATA_SIDE = ['data_loader', 'pool_screening_v2', 'features_daily', 'event_study', 'comprehensive_factor_diagnosis', 'e6j_core', 'e6j_prod',
             'e6j_features', 'e6j_slot', 'e6l_core', 'e6l_state', 'e6m_core', 'e6m_ops', 'e6m_b3_tools', 'e6m_a0', 'e6m_adapter']
ACCOUNT_SIDE = ['e6k_env']


def run(targets):
    code = PROBE % dict(code=M.CODE, targets=targets)
    p = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, cwd=M.CODE)
    line = [l for l in p.stdout.split('\n') if l.startswith('__JSON__')]
    if not line:
        return dict(targets=targets, ok=False, error='子进程无输出：%s' % M.san(p.stderr[-400:]), failed_at='', project_modules=[], opened_non_code=[])
    return json.loads(line[0][len('__JSON__'):])


def main():
    data = run([t for t in DATA_SIDE if os.path.exists(os.path.join(M.CODE, t + '.py'))])
    acct = run(ACCOUNT_SIDE)
    rows = []
    for side, r in (('DATA_SIDE', data), ('ACCOUNT_SIDE', acct)):
        for m in r['project_modules']:
            rows.append(dict(closure=side, module=m, imported=True, is_e6e_core=(m == 'e6e_core'), note=''))
        rows.append(dict(closure=side, module='__summary__', imported=r['ok'], is_e6e_core='e6e_core' in r['project_modules'],
                         note=M.san('error=%s；failed_at=%s；import 期打开的非代码文件=%s' % (r['error'] or '无', r['failed_at'] or '无', r['opened_non_code']))))
    df = pd.DataFrame(rows)
    M.atomic_write_csv(M.P('registry', 'import_closure_E6m.csv'), df)
    datadir = os.path.realpath('/mnt/big') + os.sep               # 行情 / 结果 / 缓存所在盘（sda2 也在其下）；系统时区等库文件不算数据读取
    data_reads = [p for p in data['opened_non_code'] if p.startswith(datadir) or p.startswith(os.path.realpath(M.work()))]
    need = [M.san(p) for p in acct['opened_non_code']]
    summ = dict(data_side=dict(ok=data['ok'], n_modules=len(data['project_modules']), contains_e6e_core='e6e_core' in data['project_modules'],
                               opened_non_code=[M.san(p) for p in data['opened_non_code']], data_file_reads_at_import=[M.san(p) for p in data_reads], error=M.san(data['error'])),
                account_side=dict(ok=acct['ok'], n_modules_before_failure=len(acct['project_modules']), modules=acct['project_modules'],
                                  failed_at=acct['failed_at'], error=M.san(acct['error']), opened_non_code=need,
                                  external_inputs_needed='X01 E6 宽扫描 roles.csv（import 期）；其余 X02–X16 在运行期（见 external_inputs_E6m.csv）'),
                verdict=('数据侧闭包不含 e6e_core 且 import 期不读数据文件' if (data['ok'] and 'e6e_core' not in data['project_modules'] and not data_reads)
                         else '数据侧闭包异常（见明细）'))
    M.atomic_write_json(M.P('registry', 'import_closure_E6m.json'), summ)
    ok = data['ok'] and 'e6e_core' not in data['project_modules'] and not data_reads and not acct['ok']
    M.write_receipt(os.environ.get('E6M_TASK', 'N4_import_closure'), [M.P('registry', 'import_closure_E6m.csv'), M.P('registry', 'import_closure_E6m.json')],
                    status='SUCCEEDED' if ok else 'FAILED', code=[__file__, M.__file__], data_side_ok=data['ok'], account_side_ok=acct['ok'])
    print(json.dumps(summ, ensure_ascii=False, indent=1)[:2500])
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
