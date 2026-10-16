# -*- coding: utf-8 -*-
"""E6m 闭包门 S15 在 47 上的补充核验（决策端 2026-10-10 判据 S15-47 五项：exec_briefs/E6m_S15_E7守卫等价判据_20261010.md；
用户 2026-10-12 定"补做一份 S15 补充核验"）。只读：不改任何结果、封存件与已交付目录。
  audit    第 4 项的替代核：生产任务当时没装审计钩子，全轮 open 清单补不出来；这里在同一代码上用生产参数重放全部数据入口，
           sys.addaudithook 记 open / listdir / scandir / glob，另包 pandas.read_parquet 与 pyarrow.parquet 的读取（pyarrow 原生 IO 不触发 Python 审计事件）
  check    第 1、2、3、5 项按决策端口径核，汇总第 4 项 → supp/S15/S15_47.json / .csv、README_S15_47.md
  deliver  supp/S15/ 与本脚本拷到 handoff/E6m/stageS_supp_S15_<时间>/，写 HANDOFF_SHA256.txt
输出路径一律经 M.san 脱敏。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import json
import time
import glob
import shutil
import hashlib
import inspect
import argparse
import collections

import numpy as np
import pandas as pd

import e6m_core as M

CUT = pd.Timestamp('2026-03-27')
OUTD = M.P('supp', 'S15')
DATE_RX = re.compile(r'(?<!\d)(20\d\d)[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])(?!\d)')
SYS_MARK = ('/site-packages/', '/lib/python3', '/proc/', '/dev/', '/sys/', '/etc/', '/usr/', '/.cache/', '/numba_cache', '/e6m_numba_cache')
CODE_EXT = ('.py', '.pyc', '.so', '.pth', '.pyi')


def run_roots():
    """结果目录下的"轮次文件夹"名带时间戳（如 20261005_0556_E6m），不是行情日期：取日期时先剥掉这一段。"""
    base = os.path.dirname(os.path.normpath(M.RUNS))
    return base


def market_dates(path):
    base = run_roots()
    p = os.path.abspath(path)
    W = os.path.abspath(M.work())
    if p.startswith(W + os.sep):                     # 工作目录名本身带时间戳（E6m_stageN_20261005_0556），只看目录内的相对路径
        p = p[len(W) + 1:]
    elif p.startswith(base + os.sep):
        rest = p[len(base) + 1:].split(os.sep, 1)
        p = rest[1] if len(rest) > 1 else ''
    out = []
    for y, m, d in DATE_RX.findall(p):
        try:
            out.append(pd.Timestamp('%s-%s-%s' % (y, m, d)))
        except ValueError:
            pass
    return out


def is_data(path):
    p = os.path.abspath(path)
    return not (p.endswith(CODE_EXT) or any(s in p for s in SYS_MARK))


# ------------------------------------------------------------------ 第 4 项替代核
def task_audit():
    os.makedirs(OUTD, exist_ok=True)
    opened = collections.OrderedDict()
    listed = collections.OrderedDict()
    cur = ['(import)']

    def rec(p, how):
        try:
            p = os.path.abspath(os.fsdecode(p))
        except TypeError:
            return
        opened.setdefault(p, (how, cur[0]))

    def hook(ev, args):
        if ev == 'open' and args and isinstance(args[0], (str, bytes, os.PathLike)):
            rec(args[0], 'open')
        elif ev in ('os.listdir', 'os.scandir') and args and isinstance(args[0], (str, bytes, os.PathLike)):
            listed.setdefault(os.path.abspath(os.fsdecode(args[0])), cur[0])
        elif ev == 'glob.glob' and args:
            listed.setdefault('glob:' + str(args[0]), cur[0])
    sys.addaudithook(hook)
    import pyarrow.parquet as pq
    _rp, _rt, _pfi = pd.read_parquet, pq.read_table, pq.ParquetFile.__init__

    def rp(path, *a, **k):
        if isinstance(path, (str, bytes, os.PathLike)):
            rec(path, 'read_parquet')
        return _rp(path, *a, **k)

    def rt(source, *a, **k):
        if isinstance(source, (str, bytes, os.PathLike)):
            rec(source, 'pq.read_table')
        return _rt(source, *a, **k)

    def pfi(self, source, *a, **k):
        if isinstance(source, (str, bytes, os.PathLike)):
            rec(source, 'pq.ParquetFile')
        return _pfi(self, source, *a, **k)
    pd.read_parquet, pq.read_table, pq.ParquetFile.__init__ = rp, rt, pfi
    steps, lastdates = [], {}

    def run(name, fn):
        cur[0] = name
        t0, n0 = time.time(), len(opened)
        try:
            r = fn()
            st = 'OK'
        except Exception as e:  # noqa: BLE001
            r, st = None, 'ERROR %s' % M.san(repr(e))[:200]
        steps.append(dict(step=name, status=st, new_opened=len(opened) - n0, wall_s=round(time.time() - t0, 1)))
        print(json.dumps(steps[-1], ensure_ascii=False), flush=True)
        return r
    import e6m_s_real as RL
    import e6m_stage0_full as SF
    import e6m_s_run_masks as RM
    for s in M.SEGMENTS:
        seg = run('RL.seg_of(%s, real)：分段加载（账户 / 统计 / 附属 / 连续链 / 补充件所用）' % s, lambda s=s: RL.seg_of(s, 'real'))
        if seg is not None:
            lastdates[s] = str(pd.Timestamp(str(seg.dates[-1])).date())
        del seg
        rr = run('RM.Runner(%s, A4b, real)：名单层入口（成员特征 / 门）' % s, lambda s=s: RM.Runner(s, 'A4b', 'real'))
        del rr
    import e6f_core as F
    for s, (a, b) in sorted(SF.SEG.items()):
        run('e6f_core.guarded_load(%s, %s)：seg_i 唯一取数口' % (a, b), lambda a=a, b=b: F.guarded_load(a.replace('-', ''), b.replace('-', '')))
    run('e6m_stage0_full.load_full：全程入口（两日 d、B3 前向标签、状态序列、V 原值），FULL = %s' % (SF.FULL,), SF.load_full)
    import e6m_b6_triggers as B6
    run('e6m_b6_triggers.load：B6 触发入口', B6.load)
    import e6l_state as LS
    run("e6l_state.load_full(end='20260327')：状态序列 / 全程缓存入口", lambda: LS.load_full(end='20260327'))
    cur[0] = '(done)'
    rows = []
    for p, (how, step) in opened.items():
        dts = market_dates(p) if is_data(p) else []
        mx = max(dts) if dts else None
        rows.append(dict(path=M.san(p), how=how, step=step, data_like=is_data(p), max_date_in_path=str(mx.date()) if mx is not None else '',
                         e7_hit=bool(mx is not None and mx > CUT), sealed_or_incoming=('/sealed' in p or '/incoming/' in p)))
    O = pd.DataFrame(rows)
    M.atomic_write_csv(os.path.join(OUTD, 'audit_open_list.csv'), O)
    M.atomic_write_csv(os.path.join(OUTD, 'audit_listed_dirs.csv'), pd.DataFrame([dict(target=M.san(k), step=v) for k, v in listed.items()]))
    M.atomic_write_csv(os.path.join(OUTD, 'audit_steps.csv'), pd.DataFrame(steps))
    res = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), opened=len(O), data_like=int(O.data_like.sum()), e7_hits=int(O.e7_hit.sum()),
               sealed_or_incoming=int(O.sealed_or_incoming.sum()), steps_ok=sum(1 for x in steps if x['status'] == 'OK'), steps=len(steps),
               segment_last_dates=lastdates, max_market_date_in_paths=str(max((pd.Timestamp(x) for x in O.max_date_in_path if x), default='')))
    M.atomic_write_json(os.path.join(OUTD, 'audit_summary.json'), res)
    print(json.dumps(res, ensure_ascii=False), flush=True)
    return 0 if res['e7_hits'] == 0 and res['steps_ok'] == res['steps'] else 1


# ------------------------------------------------------------------ 第 1、2、3、5 项与汇总
def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def item1():
    import data_loader as DL
    import e6f_core as F
    E6L = os.path.join(os.path.dirname(os.path.normpath(M.RUNS)), '20260930_1141_E6l_time_memory_stage', 'source_manifest.json')
    man = json.load(open(E6L, encoding='utf-8'))

    def find(name):
        for k, v in man.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    if os.path.basename(str(kk)) == name and isinstance(vv, str):
                        return k, vv
        return None, None
    rows = []
    for mod, fn in ((DL, 'load_all_daily_data'), (F, 'guarded_load')):
        f = inspect.getsourcefile(mod)
        sec, base = find(os.path.basename(f))
        cur = sha(f)
        body = hashlib.sha256(inspect.getsource(getattr(mod, fn)).encode('utf-8')).hexdigest()
        rows.append(dict(file=os.path.basename(f), function=fn, manifest_section=sec or '—', manifest_sha256_16=(base or '')[:16], current_sha256_16=cur[:16],
                         file_equal=bool(base) and base == cur, function_body_sha256_16=body[:16]))
    ck = pd.read_csv(M.P('stage0_S', 'c1', 'checks_identity.csv'), keep_default_na=False, dtype=str)
    a14 = ck[ck.iloc[:, 0] == 'A1-4']
    ok = all(r['file_equal'] for r in rows) and (a14.iloc[:, 5] == 'PASS').all() if len(a14) and a14.shape[1] > 5 else all(r['file_equal'] for r in rows)
    return dict(item=1, name='数据入口截断常量（函数体 / 文件 sha = E6l source_manifest 只读代码基线；A1-4）', verdict='PASS' if ok else 'FAIL',
                evidence=dict(rows=rows, a1_4_rows=len(a14), a1_4_all_pass=bool(len(a14)) and bool((a14.iloc[:, 5] == 'PASS').all()) if a14.shape[1] > 5 else None,
                              baseline=M.san(E6L)))


def item2(lastdates):
    import e6j_core as J
    import e6f_core as F
    import e6m_stage0_full as SF
    import data_loader as DL
    found, later = [], []
    for mod in (J, F, SF, M, DL):
        try:
            import importlib
            m = importlib.import_module(mod.__name__)
        except Exception:  # noqa: BLE001
            continue
        for k, v in vars(m).items():
            vals = v if isinstance(v, (tuple, list)) else (v,)
            for x in vals:
                if isinstance(x, str) and DATE_RX.fullmatch(x.strip()):
                    d = market_dates(x)
                    if d and d[0] >= pd.Timestamp('2026-01-01'):
                        found.append('%s.%s=%s' % (m.__name__, k, x))
                        if d[0] > CUT:
                            later.append('%s.%s=%s' % (m.__name__, k, x))
    sig = inspect.signature(DL.load_all_daily_data).parameters.get('end_date')
    try:
        import e6l_core as LC
        lc = [k for k, v in vars(LC).items() if v is getattr(J, 'MARKET_DATA_END_MAX', None) or (isinstance(v, str) and '2026' in v and DATE_RX.fullmatch(v))]
    except Exception:  # noqa: BLE001
        lc = ['import 失败']
    rec_keys = collections.Counter()
    for p in glob.glob(M.P('task_status', '*.receipt.json')):
        try:
            r = json.load(open(p, encoding='utf-8'))
        except Exception:  # noqa: BLE001
            continue
        for k in r:
            if 'end' in k.lower() and 'max' in k.lower():
                rec_keys[k] += 1
    ok = (getattr(J, 'MARKET_DATA_END_MAX', None) == '2026-03-27' and getattr(F, 'FROZEN_END', None) == '20260327' and SF.FULL[1] == '20260327'
          and (sig is not None and sig.default == '20260327') and not later and lastdates.get('2024-2026') == '2026-03-27')
    return dict(item=2, name='各 core 冻结末日常量（= 2026-03-27）与回执末日', verdict='PASS' if ok else 'FAIL',
                evidence=dict(constants=found, later_than_cut=later, data_loader_default_end=getattr(sig, 'default', None), e6l_core_refs=lc,
                              receipt_end_max_keys=dict(rec_keys) or '回执里没有 market_data_end_max 字段（决策端写的回执名不存在）；以段上下文末日代证',
                              segment_last_dates=lastdates))


def item3():
    E = pd.read_csv(M.P('stage0_S', 'c1', 'guard_attack.csv'), keep_default_na=False, dtype=str)
    E6L = os.path.join(os.path.dirname(os.path.normpath(M.RUNS)), '20260930_1141_E6l_time_memory_stage', 'stage0', 'c1_identity_rerun', 'guard_attack.csv')
    L = pd.read_csv(E6L, keep_default_na=False, dtype=str)
    em, el = set(E.entry_id), set(L.entry_id)
    ok = (E.status == 'PASS').all() and len(em) >= len(el) + 4
    return dict(item=3, name='E7 守卫攻击矩阵（A1-5）全拦截；入口数 ≥ E6l 入口数 + 4', verdict='PASS' if ok else 'FAIL',
                evidence=dict(rows=len(E), status=E.status.value_counts().to_dict(), entries_E6m=len(em), entries_E6l=len(el), new_vs_E6l=sorted(em - el)))


def npz_dates(p):
    try:
        z = np.load(p, allow_pickle=False)
    except Exception:  # noqa: BLE001
        return None
    best = None
    for k in z.files:
        if 'date' not in k.lower():
            continue
        try:
            a = z[k]
            if a.dtype.kind in 'USO' or a.dtype.kind == 'M':
                d = pd.to_datetime(pd.Series(a.ravel()).astype(str).str[:10], errors='coerce').max()
            elif a.dtype.kind in 'iu' and a.size and a.max() > 19000000:
                d = pd.to_datetime(pd.Series(a.ravel()).astype(str), format='%Y%m%d', errors='coerce').max()
            else:
                continue
            if pd.notna(d):
                best = d if best is None else max(best, d)
        except Exception:  # noqa: BLE001
            continue
    return best


def item5():
    W = M.work()
    skip = ('replica', 'tmp', 'attempts', 'code_register')
    fam = collections.defaultdict(lambda: dict(files=0, with_dates=0, max_date=None))
    over = []
    for root, ds, fs in os.walk(W):
        rel = os.path.relpath(root, W)
        top = rel.split(os.sep)[0]
        if top in skip:
            ds[:] = []
            continue
        if top == 'stageS_dev' and rel != 'stageS_dev' and not rel.startswith(os.path.join('stageS_dev', 'meas')):
            ds[:] = []                               # stageS_dev 只扫 meas/（名单层真实运行读的测量缓存），其余是开发 / mock
            continue
        if rel == 'stageS_dev':
            ds[:] = [d for d in ds if d == 'meas']
            continue
        for f in fs:
            if not f.endswith('.npz'):
                continue
            key = os.sep.join(rel.split(os.sep)[:2]) if top in ('stageN', 'results', 'supp', 'stageS_dev') else top
            d = npz_dates(os.path.join(root, f))
            e = fam[key]
            e['files'] += 1
            if d is not None:
                e['with_dates'] += 1
                e['max_date'] = d if e['max_date'] is None else max(e['max_date'], d)
                if d > CUT:
                    over.append(os.path.join(rel, f))
    import e6m_b4 as B4
    try:
        win = B4.windows()
        wtxt = M.san(str(win))[:400]
    except Exception as e:  # noqa: BLE001
        wtxt = 'windows() 调用失败：%s' % M.san(repr(e))[:120]
    b6 = pd.read_csv(M.P('reports', 'fixed_full', 'b6_trigger_ledger.csv'), nrows=0).columns.tolist()
    fams = {k: dict(files=v['files'], with_dates=v['with_dates'], max_date=str(v['max_date'].date()) if v['max_date'] is not None else '') for k, v in sorted(fam.items())}
    ok = not over and any(v['with_dates'] for v in fams.values())
    return dict(item=5, name='账本末日 ≤ 2026-03-27（全部带日期轴的 npz：账户 / 附属 / 随机 / 连续链 / B3 / 补充件）；右删失', verdict='PASS' if ok else 'FAIL',
                evidence=dict(families=fams, over_cutoff=over[:20], b4_windows=wtxt,
                              right_censoring='输出表没有显式右删失标记列（b6_trigger_ledger 列：%s）。账户层持有窗在段末截断（e6l_fast.pnl_nb：nl = T − τ − 2），不读 E7；'
                                              'plan 第 484 行"终点超过 2026-03-27 的完整事件标右删失"在本轮表里无对应列，记为部分满足，交决策端' % ','.join(b6)))


def task_check():
    A = json.load(open(os.path.join(OUTD, 'audit_summary.json'), encoding='utf-8'))
    items = [item1(), item2(A.get('segment_last_dates', {})), item3()]
    i4 = dict(item=4, name='审计钩子 open 清单（决策端口径：本轮全部任务）', verdict='NOT_AVAILABLE',
              evidence=dict(reason='生产任务没有装 sys.addaudithook（只有 e6m_closure / e6m_x01_diag 两个诊断脚本装了），全轮 open 清单当时没有记录，事后补不出来',
                            substitute=dict(method='同一代码、生产参数重放全部数据入口，审计钩子 + parquet 读取包装记录打开的文件', **A),
                            substitute_verdict='PASS' if A['e7_hits'] == 0 and A['steps_ok'] == A['steps'] and A['sealed_or_incoming'] == 0 else 'FAIL'))
    items.append(i4)
    items.append(item5())
    items = sorted(items, key=lambda x: x['item'])
    strict = all(x['verdict'] == 'PASS' for x in items)
    res = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), basis='决策端 2026-10-10 S15-47 五项（exec_briefs/E6m_S15_E7守卫等价判据_20261010.md）；用户 2026-10-12 定补做',
               strict_all_pass=strict,
               reading='第 1、2、3、5 项按原判据；第 4 项原判据不可得，替代核 %s，是否认可由决策端定' % i4['evidence']['substitute_verdict'],
               delivered_s15='已交付闭包门的 S15 用的是执行端 10-11 两项版（A1-5 攻击矩阵 + 账户 / 随机日期轴），本核验不改它', items=items)
    M.atomic_write_json(os.path.join(OUTD, 'S15_47.json'), res)
    M.atomic_write_csv(os.path.join(OUTD, 'S15_47.csv'), pd.DataFrame([dict(item=x['item'], name=x['name'], verdict=x['verdict'],
                                                                            substitute_verdict=x['evidence'].get('substitute_verdict', '')) for x in items]))
    L = ['# E6m 闭包门 S15 在 47 上的补充核验（决策端 S15-47 五项）', '',
         '- 依据：%s。' % res['basis'],
         '- 读法：%s。' % res['reading'],
         '- 已交付的闭包门：%s。' % res['delivered_s15'],
         '- 按原判据五项全过：%s。' % ('是' if strict else '否（第 4 项原判据不可得）'), '',
         '| 项 | 内容 | 判定 | 替代核 |', '|---|---|---|---|']
    for x in items:
        L.append('| %d | %s | %s | %s |' % (x['item'], x['name'], x['verdict'], x['evidence'].get('substitute_verdict', '—')))
    L += ['', '证据明细见 `S15_47.json`；第 4 项替代核的打开清单见 `audit_open_list.csv`（路径已脱敏）、步骤见 `audit_steps.csv`、列目录见 `audit_listed_dirs.csv`。',
          '本目录只是补充核验，不改已交付目录 stageS_20261012_2222 的任何文件；脚本 `e6m_s_s15_47.py` 一并附上。', '']
    open(os.path.join(OUTD, 'README_S15_47.md'), 'w', encoding='utf-8').write(chr(10).join(L))
    print(json.dumps(dict(strict_all_pass=strict, verdicts={x['item']: x['verdict'] for x in items}, substitute=i4['evidence']['substitute_verdict']), ensure_ascii=False))
    return 0


def task_deliver():
    import e6m_s_deliver as D
    dst = os.path.join(D.HANDOFF, 'stageS_supp_S15_%s' % time.strftime('%Y%m%d_%H%M'))
    os.makedirs(dst, exist_ok=False)
    files = sorted(glob.glob(os.path.join(OUTD, '*')))
    files.append(os.path.abspath(__file__))
    lines = []
    for f in files:
        q = os.path.join(dst, os.path.basename(f))
        shutil.copy2(f, q)
        lines.append('%s  %s' % (sha(q), os.path.basename(f)))
    open(os.path.join(dst, 'HANDOFF_SHA256.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(json.dumps(dict(handoff=M.san(dst), files=len(files)), ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['audit', 'check', 'deliver'])
    a = ap.parse_args()
    return dict(audit=task_audit, check=task_check, deliver=task_deliver)[a.task]()


if __name__ == '__main__':
    sys.exit(main())
