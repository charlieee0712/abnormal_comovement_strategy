# -*- coding: utf-8 -*-
"""E6m Stage 0 · 阶段 S 项（附录 A 标 S 者；brief §5 S1）。有输入就核，没有就逐行记 SOURCE_WAIT（不跳过、不当通过）。
不读任何收益：本文件只核文件身份、代码身份、授权守卫与 E7 截止守卫。特征 / 掩码 / 映射类在 e6m_stage0_S_feat.py；
账户侧锚（A2-2 / A2-3 / A2-4 值 / A2-5 账户 / A2-6 随机）在 e6m_stage0_S_engine.py（阶段 S 才跑）。
  intake    47 拷来文件 sha 全量核对（results/E6m_copy_SHA256.txt）+ 外部输入表逐项展开（X01–X22、X27）→ PRESENT / PARTIAL / SOURCE_WAIT
  identity  A1-2 原件 sha = 各轮 MIRROR（RD 全长）/ REVIEW_input（16 位）；roles.csv 两列 = 文本重建；E5a 原件 = 仓库交付包成员
            A1-3 授权登记 + post_gate 两向实测；A1-4 代码 sha = E6l source_manifest / E6l·E6k 交付前缀；A1-5 E7 守卫攻击（真实入口）
  close     汇总全部 stage0_S 检查表 → stage0_S_summary.csv、stage0_S_gate.json（all_pass = 无 FAIL 且无 SOURCE_WAIT / NOT_RUN）
  selftest  伪造 results 根（tmp）跑 intake / identity 的文件类检查，核"该过的过、故意改坏的抓到"
状态词：PASS / FAIL / SOURCE_WAIT（输入未到）/ INFO（只记录）/ NOT_RUN（本步依赖的模块或阶段未到）。"""
import e6j_boot  # noqa: F401
import os
import re
import sys
import glob
import json
import time
import shutil
import fnmatch
import hashlib
import tarfile
import argparse
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

import e6m_core as M
import e6j_core as J

SEGS = tuple(M.SEGMENTS)
RN = dict(E6='20260904_1051_E6_wide_scan', I='20260923_0254_E6i_measurement_need_fit', J='20260927_0038_E6j_k_two_dimension_pilot',
          K='20260928_2325_E6k_k_binding_stage', L='20260930_1141_E6l_time_memory_stage', A='20260903_1214_delivery_pools_v2')
RNAME = dict(E6='E6', I='E6i', J='E6j', K='E6k', L='E6l', A='E5a')
X23 = ('delivery', 'I11_candidate_pools_v2_20260903', 'I11_candidate_pools_v2_20260903.tar.gz')
STATUSES = ('PASS', 'FAIL', 'SOURCE_WAIT', 'INFO', 'NOT_RUN')
OPTIONAL_PREFIX = ('randoms/',)                     # 拷贝请求允许最后单独补的子树：缺 → SOURCE_WAIT 而非 FAIL
# 外部输入展开（registry/external_inputs_E6m.csv 的机器版；{seg} 展开四段；最后一项 = 每个模式至少命中数）
EXT = {
    'X01': [('E6', 'roles.csv', 1)],
    'X02': [('I', 'registration/record_B_approved_E6i.json', 1)],
    'X03': [('I', 'cache/{seg}/%s__OBS.%s' % (m, e), 1) for m in ('K_rar20', 'K_slope20', 'K_MA3_E6F') for e in ('npy', 'json')],
    'X04': [('J', 'cache/{seg}/J_B1_qCC.%s' % e, 1) for e in ('npy', 'json')],
    'X05': [('J', 'registry/trade_calendar.csv', 1)],
    'X06': [('J', 'anchors/mother_ledger_prod_v2.parquet', 1)],
    'X07': [('J', 'results_P/pilot_policy.csv', 1), ('J', 'results_B/part2_main_config_all_objects.csv', 1),
            ('J', 'stage0/anchor2_rerun/e6i_parent_anchor.csv', 1)],
    'X08': [('J', 'carried/leader_six_forms_capital.csv', 1), ('J', 'accounts/B/{seg}/*.npz', 1)],
    'X09': [('I', 'accounts/{seg}/merged_index.csv', 1)],
    'X10': [('A', 'summary.csv', 1), ('A', 'pool1_I11_screening.csv', 1), ('A', 'pool2_*.csv', 6)],
    'X11': [('K', 'results/full/policy_E6k.csv', 1)],
    'X12': [('K', 'registry/descriptors_E6k.csv', 1)],
    'X13': [('K', 'registry/accessory_E6k.csv', 1), ('K', 'registry/randoms_E6k.csv', 1), ('K', 'results/full/random_refs_{seg}.csv', 1),
            ('K', 'source_manifest.json', 1), ('K', 'engine_contract.md', 1)],
    'X14': [('K', 'registry/mask_facts_deriv_E6k.csv', 1), ('K', 'registry/mask_facts_post_E6k.csv', 1)],
    'X15': [('K', 'registration/policy_profiles_E6k.json', 1), ('K', 'registration/policy_profiles_E6k_amend_1.json', 1),
            ('K', 'registration/policy_profiles_E6k_amend_2.json', 1)],
    'X16': [('K', 'accounts/{seg}/*.npz', 1)],
    'X17': [('L', 'results/full/policy_E6l.csv', 1)],
    'X18': [('L', 'registry/descriptors_E6l.csv', 1), ('L', 'results/stage_a/mask_facts_deriv_E6l.csv', 1),
            ('L', 'results/stage_a/mask_facts_post_E6l.csv', 1)],
    'X19': [('L', 'registration/policy_profiles_E6l.json', 1)],
    'X20': [('L', 'results/full/random_refs_{seg}.csv', 1)],
    'X21': [('L', 'cache/state/state_full_E6l.npz', 1)],
    'X22': [('L', 'results/full/*.csv', 1)],
    'X27': [('I', 'cache/{seg}/V_park20_LEGACY__LEGACY_PARK_NAN.npy', 1), ('I', 'cache/{seg}/V_park20_LEGACY__LEGACY_PARK_NAN.json', 1)],
}


def default_root():
    r = os.path.dirname(J.E6I_RES)
    if os.path.join(r, RN['I']) != J.E6I_RES or os.path.join(r, RN['A']) != J.E5A_RES:
        raise RuntimeError('results 根与 e6j_core 常量不一致')
    return r


def refs_dir():
    return M.P('stage0_S', 'refs')


def sha256(p, bs=8 << 20):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        while True:
            b = fh.read(bs)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class Hasher(object):
    """全长 sha256 缓存（同一文件一轮只算一次；8 线程流式读，hashlib 大块释放 GIL）。"""

    def __init__(self, workers=8):
        self.cache, self.workers = {}, workers

    def many(self, paths):
        todo = sorted(set(p for p in paths if p not in self.cache and os.path.isfile(p)))
        if todo:
            with ThreadPoolExecutor(self.workers) as ex:
                for p, s in zip(todo, ex.map(sha256, todo)):
                    self.cache[p] = s
        return {p: self.cache.get(p) for p in paths}

    def one(self, p):
        return self.many([p])[p]


class Book(object):
    COLS = ['item', 'object', 'metric', 'expected', 'got', 'status', 'note']

    def __init__(self):
        self.rows = []

    def add(self, item, obj, metric, expected, got, status, note=''):
        if status not in STATUSES:
            raise ValueError(status)
        self.rows.append(dict(item=item, object=M.san(obj), metric=metric, expected=M.san(str(expected)), got=M.san(str(got)), status=status,
                              note=M.san(str(note))))

    def ok(self, item, obj, metric, expected, got, cond, note=''):
        self.add(item, obj, metric, expected, got, 'PASS' if cond else 'FAIL', note)

    def df(self):
        return pd.DataFrame(self.rows, columns=self.COLS)

    def write(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df = self.df()
        M.atomic_write_csv(path, df)
        return df


# ====================================================================== intake
def expand(root, spec):
    rr, pat, mn = spec
    base = os.path.join(root, RN[rr])
    pats = [pat.replace('{seg}', s) for s in SEGS] if '{seg}' in pat else [pat]
    return [(os.path.join(RN[rr], p), sorted(glob.glob(os.path.join(base, p))), mn) for p in pats]


def copy_list(root):
    """results/E6m_copy_SHA256.txt（47 上 sha256sum 生成；路径相对 results 根）→ [(相对路径, sha)]。"""
    lst = os.path.join(root, 'E6m_copy_SHA256.txt')
    if not os.path.exists(lst):
        return None
    out = []
    for ln in open(lst, encoding='utf-8'):
        p = ln.rstrip('\n').split(None, 1)
        if len(p) == 2 and re.fullmatch(r'[0-9a-f]{64}', p[0]):
            r = p[1].strip()
            r = r[1:] if r.startswith('*') else r
            r = r[2:] if r.startswith('./') else r
            out.append((r, p[0]))
    return out


def task_intake(root, out, H):
    B = Book()
    od = os.path.join(out, 'intake')
    os.makedirs(od, exist_ok=True)
    cl = copy_list(root)
    if cl is None:
        if M.MACHINE == '47':   # 47 上原位读取外部输入，没有拷贝这一步（2026-10-09）
            B.add('A0-S', 'results/E6m_copy_SHA256.txt', '47 拷贝 sha 清单全量核对', '清单存在', 'NOT_APPLICABLE：在 47 原位读取，无拷贝', 'INFO',
                  '外部输入身份另由 A1-2 原件 sha 核')
        else:
            B.add('A0-S', 'results/E6m_copy_SHA256.txt', '47 拷贝 sha 清单全量核对', '清单存在', '缺', 'SOURCE_WAIT', '文件未拷到云机')
    else:
        got = H.many([os.path.join(root, r) for r, _ in cl])
        rows = [dict(file=r, expected_sha256=s, sha256=got[os.path.join(root, r)] or 'MISSING',
                     status='PASS' if got[os.path.join(root, r)] == s else 'FAIL') for r, s in cl]
        df = pd.DataFrame(rows)
        M.atomic_write_csv(os.path.join(od, 'copy_sha_check.csv'), df)
        nbad = int((df.status != 'PASS').sum())
        B.ok('A0-S', 'results/E6m_copy_SHA256.txt', '47 拷贝 sha 全量核对（sha256sum -c 同义）', '%d 文件全 PASS' % len(df), '%d FAIL' % nbad, nbad == 0)
    ext = M.read_csv_keep(M.P('registry', 'external_inputs_E6m.csv'), dtype=str)
    files, xs = [], {}
    for xid, specs in EXT.items():
        parts = [e for s in specs for e in expand(root, s)]
        allh = [h for _, hits, _ in parts for h in hits]
        shas = H.many(allh)
        nok = sum(len(hits) >= mn for _, hits, mn in parts)
        st = 'PRESENT' if nok == len(parts) else ('SOURCE_WAIT' if not allh else 'PARTIAL')
        for pat, hits, mn in parts:
            for h in hits:
                files.append(dict(id=xid, pattern=pat, file=os.path.relpath(h, root), bytes=os.path.getsize(h), sha256=shas[h]))
            if len(hits) < mn:
                files.append(dict(id=xid, pattern=pat, file='', bytes=-1, sha256='SOURCE_WAIT' if not hits else 'PARTIAL（%d < %d）' % (len(hits), mn)))
        if len(allh) == 1:
            sh = shas[allh[0]]
        elif allh:
            sh = 'LIST:' + M.sha_bytes('\n'.join('%s %s' % (os.path.relpath(h, root), shas[h]) for h in sorted(allh)).encode('utf-8'))
        else:
            sh = ''
        xs[xid] = (st, sh, len(allh))
        B.add('A0-S', xid, '外部输入展开（%d 个模式，命中 %d 文件）' % (len(parts), len(allh)), 'PRESENT', st,
              {'PRESENT': 'PASS', 'SOURCE_WAIT': 'SOURCE_WAIT'}.get(st, 'FAIL'), '' if st != 'PARTIAL' else '部分文件缺：见 external_inputs_files.csv')
    M.atomic_write_csv(os.path.join(od, 'external_inputs_files.csv'), pd.DataFrame(files, columns=['id', 'pattern', 'file', 'bytes', 'sha256']))
    E = ext.copy()
    for i, r in E.iterrows():
        if r['id'] in xs:
            st, sh, n = xs[r['id']]
            E.at[i, 'status'] = st
            E.at[i, 'sha256'] = sh
    M.atomic_write_csv(os.path.join(od, 'external_inputs_E6m_S.csv'), E)
    return B


# ====================================================================== identity
def mirror_rd(path):
    """MIRROR.md5 的 RD（结果目录）行 → {相对路径: [sha256 全长…]}。"""
    out = {}
    for ln in open(path, encoding='utf-8'):
        p = ln.split()
        if len(p) >= 4 and re.fullmatch(r'[0-9a-f]{32}', p[0]) and re.fullmatch(r'[0-9a-f]{64}', p[1]) and p[2] == 'RD':
            out.setdefault(p[3], []).append(p[1])
    return out


def review_prefixes(path):
    """REVIEW_input 的 `路径`（16 位）→ {路径: [前缀…]}；含占位符 / 通配的路径不收。"""
    out = {}
    for pth, h in re.findall(r'`([^`\s]+)`（([0-9a-f]{16})）', open(path, encoding='utf-8').read()):
        if any(ch in pth for ch in '<*{'):
            continue
        out.setdefault(pth, []).append(h)
    return out


def bound_patterns(rr):
    """本轮实际读取的原件（外部输入表 X01–X22 / X27 的机器展开）在该轮结果目录里的相对路径模式。"""
    return [pat.replace('{seg}', '*') for specs in EXT.values() for r, pat, mn in specs if r == rr]


def a1_2(B, root, H, refs):
    for rr in ('I', 'J', 'K', 'L'):
        rn = RNAME[rr]
        base = os.path.join(root, RN[rr])
        mir = os.path.join(refs, '%s_MIRROR.md5' % rn)
        rin = os.path.join(refs, '%s_REVIEW_input.md' % rn)
        full = mirror_rd(mir) if os.path.exists(mir) else {}
        pre = review_prefixes(rin) if os.path.exists(rin) else {}
        if not (full or pre):
            B.add('A1-2', rn, 'MIRROR / REVIEW_input 参照', '存在', '缺', 'FAIL', '参照文件应在 stage0_S/refs/')
            continue
        paths = sorted(set(full) | set(p for p in pre if not p.startswith(('code/', 'exec_briefs/'))))
        if not os.path.isdir(base):
            B.add('A1-2', rn, '原件（%d 条参照）' % len(paths), '可读 + sha 一致', '结果目录未到', 'SOURCE_WAIT')
            continue
        shas = H.many([os.path.join(base, p) for p in paths])
        pats = bound_patterns(rr)
        nb = nbp = no = nop = 0
        for p in paths:
            fp = os.path.join(base, p)
            s = shas[fp]
            bound = any(fnmatch.fnmatch(p, q) for q in pats)        # 本轮实际读取的文件（X01–X22 / X27）才约束 Stage 0 门；其余参照只记 INFO
            nb += bound
            no += not bound
            exp = ['全长 ' + x for x in full.get(p, [])] + ['前缀 ' + x for x in pre.get(p, [])]
            if s is None:
                B.add('A1-2', '%s %s' % (rn, p), 'sha = MIRROR / REVIEW_input%s' % ('' if bound else '（E6m 不读，INFO）'), ' | '.join(exp), '缺',
                      ('SOURCE_WAIT' if p.startswith(OPTIONAL_PREFIX) else 'FAIL') if bound else 'INFO')
                continue
            ok = (not full.get(p) or s in full[p]) and (not pre.get(p) or any(s.startswith(x) for x in pre[p]))
            if bound:
                nbp += ok
            else:
                nop += ok
            if not ok:
                B.add('A1-2', '%s %s' % (rn, p), 'sha = MIRROR / REVIEW_input%s' % ('' if bound else '（E6m 不读，INFO）'), ' | '.join(exp), s,
                      'FAIL' if bound else 'INFO')
        B.add('A1-2', rn, '本轮读取的原件 sha 一致 / 参照条数', nb, nbp, 'INFO', '逐条 FAIL / 缺件另列')
        B.add('A1-2', rn, '其余参照文件（E6m 不读）sha 一致 / 条数', no, nop, 'INFO', '不约束 Stage 0 门（STAGE_S_IMPL_PLAN §5 第 20 项）')
    # E6 宽扫描 roles.csv（X01）：e6e_core 只用 factor / worst_pooled 两列 → 与文本重建逐行
    rp = os.path.join(root, RN['E6'], 'roles.csv')
    recon = M.read_csv_keep(M.P('registry', 'x01_roles_text_reconstructed.csv'))
    if not os.path.exists(rp):
        B.add('A1-2', 'E6 roles.csv（X01）', '存在 + factor / worst_pooled = 文本重建', '35 行一致', '未到', 'SOURCE_WAIT')
    else:
        R = pd.read_csv(rp)
        B.add('A1-2', 'E6 roles.csv（X01）', 'sha256（INFO；权威核对 = 拷贝清单）', '', H.one(rp), 'INFO')
        miss = [c for c in ('factor', 'worst_pooled') if c not in R.columns]
        if miss:
            B.add('A1-2', 'E6 roles.csv（X01）', '列存在', 'factor / worst_pooled', '缺 %s' % miss, 'FAIL')
        else:
            a = recon.set_index('factor').worst_pooled.astype(int)
            b = R.drop_duplicates('factor').set_index('factor').worst_pooled
            bad = [f for f in a.index if f not in b.index or int(b[f]) != int(a[f])]
            B.ok('A1-2', 'E6 roles.csv（X01）', 'factor → worst_pooled 与文本重建逐行（%d 行）' % len(a), '0 不一致', '%d 不一致：%s' % (len(bad), bad[:5]),
                 not bad)
            extra = sorted(set(b.index) - set(a.index))
            B.add('A1-2', 'E6 roles.csv（X01）', '原件多出的 factor（INFO）', '', '%d：%s' % (len(extra), extra[:5]), 'INFO')
    # E5a 原件 = 仓库交付包成员（X10 vs X23）
    ad = os.path.join(root, RN['A'])
    tz = os.path.join(M.CODE, *X23)
    if not os.path.isdir(ad):
        B.add('A1-2', 'E5a 交付池（X10）', '逐字节 = 仓库交付包成员（X23）', '7 文件一致', '结果目录未到', 'SOURCE_WAIT')
    else:
        with tarfile.open(tz, 'r:gz') as tf:
            mem = {os.path.basename(m.name): hashlib.sha256(tf.extractfile(m).read()).hexdigest() for m in tf.getmembers() if m.isfile()}
        for f, s in sorted(mem.items()):
            fp = os.path.join(ad, f)
            got = H.one(fp) if os.path.exists(fp) else 'MISSING'
            B.ok('A1-2', 'E5a %s' % f, '逐字节 = 仓库交付包成员', s, got, got == s)
        sp = os.path.join(ad, 'summary.csv')
        B.add('A1-2', 'E5a summary.csv', 'sha（交付包无此文件；6bp 逐列在 engine A2-2）', '', H.one(sp) if os.path.exists(sp) else '未到',
              'INFO' if os.path.exists(sp) else 'SOURCE_WAIT')


def a1_3(B, tmp):
    import e6m_s_gate as G
    reg = M.P('registration')
    for f, what in (('authorization_status_E6m.json', 'W11 方式登记（N）'), ('record_B_mode_A.json', '方式 A 记录（N）')):
        p = os.path.join(reg, f)
        B.ok('A1-3', 'registration/' + f, what, '存在', '存在' if os.path.exists(p) else '缺', os.path.exists(p))
    p = M.P('stageN', 'B3_prelim_authorization.json')
    B.ok('A1-3', 'stageN/B3_prelim_authorization.json', 'N8 授权词单独登记', '存在', '存在' if os.path.exists(p) else '缺', os.path.exists(p))
    for r in G.two_way(tmp):
        B.ok('A1-3', 'e6m_s_gate.post_gate', r['case'], r['expect'], r['got'], r['ok'])


def a1_4(B, root, H, refs):
    code = M.CODE
    man = os.path.join(root, RN['L'], 'source_manifest.json')
    if not os.path.exists(man):
        B.add('A1-4', 'E6l source_manifest.readonly_code_sha256', '四地基 + e6e–e6l 文件 sha = manifest', '全一致', '清单未到', 'SOURCE_WAIT')
    else:
        sm = json.load(open(man, encoding='utf-8'))
        ro = sm.get('readonly_code_sha256', {})
        cur = H.many([os.path.join(code, f) for f in ro])
        bad = [f for f, s in ro.items() if cur[os.path.join(code, f)] != s]
        B.ok('A1-4', 'E6l source_manifest.readonly_code_sha256', '%d 文件 sha = manifest' % len(ro), '0 不一致', '%d：%s' % (len(bad), bad[:8]), not bad)
        for f in bad:
            B.add('A1-4', f, 'sha = E6l manifest', ro[f], cur[os.path.join(code, f)] or 'MISSING', 'FAIL')
    for rn in ('E6l', 'E6k'):
        rin = os.path.join(refs, '%s_REVIEW_input.md' % rn)
        if not os.path.exists(rin):
            B.add('A1-4', '%s REVIEW_input' % rn, '交付代码前缀', '参照存在', '缺', 'FAIL')
            continue
        pre = {p[5:]: v for p, v in review_prefixes(rin).items() if p.startswith('code/')}
        cur = H.many([os.path.join(code, f) for f in pre])
        n_ok = 0
        for f, v in sorted(pre.items()):
            s = cur[os.path.join(code, f)]
            ok = s is not None and any(s.startswith(x) for x in v)
            n_ok += ok
            if not ok:
                B.add('A1-4', f, 'sha 前缀 = %s 交付版（REVIEW_input）' % rn, '|'.join(v), (s or 'MISSING')[:16], 'FAIL')
        B.add('A1-4', '%s 交付代码' % rn, '前缀一致数 / 列出数', len(pre), n_ok, 'PASS' if n_ok == len(pre) else 'FAIL')


def a1_5(B, root, tmp):
    """E7 守卫攻击（真实入口；E6l G1–G12 + 本轮入口）。攻击只用合成未来日期 / 伪造 sidecar，写 tmp。"""
    os.makedirs(tmp, exist_ok=True)
    rows = []

    def add(gid, entry, attack, status, detail=''):
        rows.append(dict(entry_id=gid, entry=entry, attack=attack, status=status, detail=M.san(str(detail))[:200]))

    def raises(fn):
        try:
            fn()
        except (RuntimeError, ValueError, AssertionError) as e:
            return True, repr(e)[:160]
        return False, 'no exception'

    def okst(c):
        return 'PASS' if c else 'FAIL'
    import e6j_prod as PR
    calls = []
    orig = PR.load_all_daily_data
    PR.load_all_daily_data = lambda *a, **k: calls.append((a, k))
    PR.PERIODS['__ATTACK__'] = ('20260301', '20260410')
    try:
        ok, why = raises(lambda: PR.build_period('__ATTACK__'))
        add('G1', 'e6j_prod.build_period（tmp/ctx_<段>.pkl 与 MockSeg 的来源）', "段 ('20260301','20260410')", okst(ok and not calls),
            '%s; load calls=%d' % (why, len(calls)))
        import e6m_stage0_data as SD
        ok, why = raises(lambda: SD.task_seg('__ATTACK__', 0))
        add('G13', 'e6m_stage0_data.task_seg（E6m 段上下文入口）', "段 ('20260301','20260410')", okst(ok and not calls), why)
    finally:
        del PR.PERIODS['__ATTACK__']
        PR.load_all_daily_data = orig
    import e6m_stage0_full as SF
    import data_loader as DL
    fake = os.path.join(tmp, 'fake_cache_full')
    os.makedirs(fake, exist_ok=True)
    o_full, o_cd, o_load = SF.FULL, SF.cache_dir, DL.load_all_daily_data
    SF.FULL = ('20100101', '20260410')
    for f in ['daily_kline_%s_%s.parquet' % SF.FULL] + ['ftl_%s.parquet' % x for x in SF.FTL]:
        open(os.path.join(fake, f), 'wb').close()
    SF.cache_dir = lambda: fake
    lc = []
    DL.load_all_daily_data = lambda *a, **k: lc.append(1)
    try:
        ok, why = raises(SF.load_full)
        add('G14', 'e6m_stage0_full.load_full（全程入口：两日 d、B3 前向标签、状态序列、V 原值）', "FULL end='20260410'（缓存件伪造齐全）",
            okst(ok and not lc and '缓存缺件' not in why), why)
        import e6m_b6_triggers as B6
        ok, why = raises(B6.load)
        add('G17', 'e6m_b6_triggers.load（B6 触发入口）', "FULL end='20260410'（缓存件伪造齐全）", okst(ok and not lc and '缓存缺件' not in why), why)
    finally:
        SF.FULL, SF.cache_dir, DL.load_all_daily_data = o_full, o_cd, o_load
    if 'e6f_core' in sys.modules or os.path.exists(os.path.join(root, RN['E6'], 'roles.csv')):
        import e6f_core as F
        ok, why = raises(lambda: F.guarded_load('20260301', '20260401'))
        add('G2', 'e6f_core.guarded_load（seg_i 唯一取数口）', "guarded_load('20260301','20260401')", okst(ok), why)
    else:
        add('G2', 'e6f_core.guarded_load（seg_i 唯一取数口）', "guarded_load('20260301','20260401')", 'SOURCE_WAIT', 'X01 未到：e6f_core import 期读 roles.csv')
    import e6j_slot as SL
    fk = os.path.join(tmp, 'fake_member_cache')
    os.makedirs(os.path.join(fk, '2024-2026'), exist_ok=True)
    arr = np.zeros((3, 2))
    for nm in ('FAKE__OBS', 'FAKE_J'):
        pth = os.path.join(fk, '2024-2026', nm + '.npy')
        np.save(pth, arr)
        json.dump(dict(shape=[3, 2], sha256=J.sha_file(pth), max_feature_date='2026-04-01', segment='2024-2026', synthetic=True),
                  open(pth[:-4] + '.json', 'w'))
    o3, o4 = SL.E6I_CACHE, SL.J_CACHE
    SL.E6I_CACHE = SL.J_CACHE = fk
    try:
        ok, why = raises(lambda: SL.e6i_member_raw('2024-2026', 'FAKE'))
        add('G3', 'e6j_slot.e6i_member_raw', 'sidecar max_feature_date=2026-04-01', okst(ok), why)
        ok, why = raises(lambda: SL.j_member_raw('2024-2026', 'FAKE_J'))
        add('G4', 'e6j_slot.j_member_raw', 'sidecar max_feature_date=2026-04-01', okst(ok), why)
    finally:
        SL.E6I_CACHE, SL.J_CACHE = o3, o4
    ok, why = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327, 20260330]), 'attack'))
    add('G5', 'e6j_core.assert_index_ok', '索引含 20260330', okst(ok), why)
    ok2, _ = raises(lambda: J.assert_index_ok(pd.Index([20260325, 20260327]), 'ok'))
    add('G5b', 'e6j_core.assert_index_ok', '合法索引（止于 20260327）不应误报', okst(not ok2))
    import e6j_random as R
    calp = os.path.join(root, RN['J'], 'registry', 'trade_calendar.csv')
    if os.path.exists(calp):
        cal = pd.Index(pd.to_datetime(pd.read_csv(calp).date))
        ok, why = raises(lambda: R.Grid(pd.to_datetime(['2026-03-27', '2026-03-30']), ['000001.SZ'], cal))
        add('G6', 'e6j_random.Grid / day_index', '日期 2026-03-30 不在日历', okst(ok), why)
        add('G6b', 'E6j registry/trade_calendar.csv', '日历末日 ≤ 截止', okst(str(cal.max().date()) <= M.MARKET_DATA_END_MAX), str(cal.max().date()))
    else:
        add('G6', 'e6j_random.Grid / day_index', '日期 2026-03-30 不在日历', 'SOURCE_WAIT', 'X05 未到')
        add('G6b', 'E6j registry/trade_calendar.csv', '日历末日 ≤ 截止', 'SOURCE_WAIT', 'X05 未到')
    lp = os.path.join(root, RN['J'], 'anchors', 'mother_ledger_prod_v2.parquet')
    if os.path.exists(lp):
        led = pd.read_parquet(lp, columns=['date'])
        add('G7a', 'E6j anchors/mother_ledger_prod_v2.parquet', '账本末日 ≤ 截止', okst(str(led.date.max())[:10] <= M.MARKET_DATA_END_MAX), led.date.max())
    else:
        add('G7a', 'E6j anchors/mother_ledger_prod_v2.parquet', '账本末日 ≤ 截止', 'SOURCE_WAIT', 'X06 未到')
    for gid, rr, pat, what in (('G7b', 'J', 'cache/*/*.json', 'E6j J 成员'), ('G7c', 'I', 'cache/*/*__OBS.json', 'E6i 成员（含 parkinson）')):
        js = glob.glob(os.path.join(root, RN[rr], pat))
        if js:
            mx = max(str(json.load(open(p, encoding='utf-8')).get('max_feature_date', '9999')) for p in js)
            add(gid, '%s sidecar' % what, 'max_feature_date 最大值 ≤ 截止（%d 个）' % len(js), okst(mx <= M.MARKET_DATA_END_MAX), mx)
        else:
            add(gid, '%s sidecar' % what, 'max_feature_date 最大值 ≤ 截止', 'SOURCE_WAIT', '缓存未到')
    sp = os.path.join(root, RN['L'], 'cache', 'state', 'state_full_E6l.npz')
    if os.path.exists(sp):
        z = np.load(sp, allow_pickle=False)
        d = max(str(x)[:10] for x in np.asarray(z['dates']).tolist())
        add('G7d', 'E6l cache/state/state_full_E6l.npz', '状态日期末日 ≤ 截止', okst(d <= M.MARKET_DATA_END_MAX), d)
    else:
        add('G7d', 'E6l cache/state/state_full_E6l.npz', '状态日期末日 ≤ 截止', 'SOURCE_WAIT', 'X21 未到')
    import e6m_s_gate as GT
    emp = os.path.join(tmp, 'gate_empty')
    os.makedirs(emp, exist_ok=True)
    ok, why = raises(lambda: GT.post_gate('2019-2023', 'attack', root=emp))
    add('G8', 'e6m_s_gate.post_gate', '无 E6m 授权文件时计算后段新对象', okst(ok), why)
    ok, why = raises(lambda: GT.deriv_only('2024-2026', 'attack'))
    add('G9', 'e6m_s_gate.deriv_only', '推导段限定步骤调用后段', okst(ok), why)
    import e6l_state as LS
    ok, why = raises(lambda: LS.load_full(end='20260410'))
    add('G10', 'e6l_state.load_full（全程缓存入口）', "end='20260410'", okst(ok), why)
    ok, why = raises(lambda: LS.assert_state_dates(pd.to_datetime(['2026-03-27', '2026-03-30'])))
    add('G11', 'e6l_state.assert_state_dates（状态序列入口）', '状态日期含 2026-03-30', okst(ok), why)
    ok, why = raises(lambda: LS.full_period_ctx(end='20260410', dry_run=True))
    add('G12', 'e6l_state.full_period_ctx（连续面板入口）', "end='20260410'", okst(ok), why)
    ok2, _ = raises(lambda: LS.full_period_ctx(end='20260327', dry_run=True))
    add('G12b', 'e6l_state.full_period_ctx', "end='20260327' 不应误报", okst(not ok2))
    zs = M.P('stage0', 'cache_cloud', 'state_full_E6m_cloud.npz')
    if os.path.exists(zs):
        d = max(str(x)[:10] for x in np.load(zs, allow_pickle=False)['dates'].tolist())
        add('G15', 'E6m stage0/cache_cloud/state_full_E6m_cloud.npz', '云机状态缓存末日 ≤ 截止', okst(d <= M.MARKET_DATA_END_MAX), d)
    for seg in SEGS:
        pk = M.P('tmp', 'ctx_%s.pkl' % seg)
        if os.path.exists(pk):
            import pickle
            with open(pk, 'rb') as fh:
                ctx = pickle.load(fh)
            d = str(ctx['pool0'].index.max())[:10]
            add('G16', 'E6m tmp/ctx_%s.pkl（段上下文：mock / 测量 / B3 掩码）' % seg, 'pool0 末日 ≤ 截止', okst(d <= M.MARKET_DATA_END_MAX), d)
            del ctx
    df = pd.DataFrame(rows)
    M.atomic_write_csv(os.path.join(B.out, 'guard_attack.csv'), df)
    for r in rows:
        B.add('A1-5', r['entry'], r['attack'], 'raise / 静态末日 ≤ 截止', r['detail'], r['status'])
    shutil.rmtree(tmp, ignore_errors=True)
    return df


def task_identity(root, out, H, refs):
    B = Book()
    B.out = os.path.join(out, 'c1')
    os.makedirs(B.out, exist_ok=True)
    a1_2(B, root, H, refs)
    a1_3(B, M.P('tmp', 'stage0_S_post_gate_two_way'))
    a1_4(B, root, H, refs)
    a1_5(B, root, M.P('tmp', 'stage0_S_guard_attack'))
    return B


# ====================================================================== close
def task_close(out):
    """mock/（mock 结构上的 B2 证据）与 selftest/（夹具自测）不计入 Stage 0 门。"""
    fs = sorted(f for f in glob.glob(os.path.join(out, '*', 'checks_*.csv')) if os.path.basename(os.path.dirname(f)) not in ('mock', 'selftest'))
    D = pd.concat([M.read_csv_keep(f, dtype=str).assign(table=os.path.relpath(f, out)) for f in fs], ignore_index=True) if fs else pd.DataFrame()
    S = D.groupby(['item', 'status']).size().unstack(fill_value=0).reset_index() if len(D) else pd.DataFrame()
    p1 = os.path.join(out, 'stage0_S_summary.csv')
    M.atomic_write_csv(p1, S)
    cnt = D.status.value_counts().to_dict() if len(D) else {}
    gate = dict(written_at=time.strftime('%Y-%m-%d %H:%M:%S'), tables=[os.path.relpath(f, out) for f in fs], counts=cnt,
                fail_items=sorted(set(D[D.status == 'FAIL'].item)) if len(D) else [], source_wait_items=sorted(set(D[D.status == 'SOURCE_WAIT'].item)) if len(D) else [],
                not_run_items=sorted(set(D[D.status == 'NOT_RUN'].item)) if len(D) else [],
                all_pass=bool(len(D)) and not any(cnt.get(k, 0) for k in ('FAIL', 'SOURCE_WAIT', 'NOT_RUN')))
    p2 = os.path.join(out, 'stage0_S_gate.json')
    M.atomic_write_json(p2, gate)
    return p1, p2, gate


# ====================================================================== selftest（伪造 results 根）
def task_selftest(out, H):
    """伪造 results 根：E6l 目录放 3 个 REVIEW_input 列出的文件（2 个按参照 sha 不可能一致 → 应 FAIL；1 个参照不收 → 不出现），
    roles.csv = 文本重建原样（应 PASS）与改坏一行（应 FAIL）；拷贝清单 2 行（1 对 1 错）；E5a 放交付包成员原字节（应 PASS）。"""
    fx = M.P('tmp', 'stage0_S_fixture')
    shutil.rmtree(fx, ignore_errors=True)
    root = os.path.join(fx, 'results')
    os.makedirs(os.path.join(root, RN['E6']))
    rec = M.read_csv_keep(M.P('registry', 'x01_roles_text_reconstructed.csv'))
    rec.to_csv(os.path.join(root, RN['E6'], 'roles.csv'), index=False)
    os.makedirs(os.path.join(root, RN['L'], 'results', 'full'))
    for f in ('policy_E6l.csv', 'random_refs.csv'):
        with open(os.path.join(root, RN['L'], 'results', 'full', f), 'w') as fh:
            fh.write('synthetic,fixture\n1,2\n')
    ad = os.path.join(root, RN['A'])
    os.makedirs(ad)
    with tarfile.open(os.path.join(M.CODE, *X23), 'r:gz') as tf:
        for m in tf.getmembers():
            if m.isfile():
                with open(os.path.join(ad, os.path.basename(m.name)), 'wb') as fh:
                    fh.write(tf.extractfile(m).read())
    r1 = os.path.join(RN['E6'], 'roles.csv')
    with open(os.path.join(root, 'E6m_copy_SHA256.txt'), 'w') as fh:
        fh.write('%s  %s\n' % (sha256(os.path.join(root, r1)), r1))
        fh.write('%s  %s\n' % ('0' * 64, os.path.join(RN['L'], 'results', 'full', 'policy_E6l.csv')))
    Hx = Hasher()
    BI = task_intake(root, os.path.join(fx, 'out'), Hx)
    BD = Book()
    BD.out = os.path.join(fx, 'out', 'c1')
    os.makedirs(BD.out, exist_ok=True)
    a1_2(BD, root, Hx, refs_dir())
    exp = []
    di, dd = BI.df(), BD.df()
    exp.append(('intake 拷贝清单 1 错 → FAIL', ((di.item == 'A0-S') & di.object.str.contains('E6m_copy') & (di.status == 'FAIL')).sum() == 1))
    exp.append(('X01 → PRESENT（PASS）', ((di.object == 'X01') & (di.status == 'PASS')).sum() == 1))
    exp.append(('X17 → PRESENT（PASS）', ((di.object == 'X17') & (di.status == 'PASS')).sum() == 1))
    exp.append(('X11 → SOURCE_WAIT', ((di.object == 'X11') & (di.status == 'SOURCE_WAIT')).sum() == 1))
    exp.append(('X10 → PARTIAL（FAIL：summary.csv 缺）', ((di.object == 'X10') & (di.status == 'FAIL')).sum() == 1))
    exp.append(('roles.csv 文本重建 → PASS', (dd.object.str.contains('roles.csv') & dd.metric.str.contains('逐行') & (dd.status == 'PASS')).sum() == 1))
    exp.append(('E6l policy_E6l.csv 伪造 → FAIL', (dd.object.str.contains('E6l results/full/policy_E6l.csv') & (dd.status == 'FAIL')).sum() == 1))
    exp.append(('E6l 本轮读取的原件缺 → FAIL', ((dd.object.str.startswith('E6l ')) & (dd.got == '缺') & (dd.status == 'FAIL')).sum() > 0))
    rep = dd.object.str.startswith('E6l reports/')
    exp.append(('E6l 本轮不读的参照（reports/）缺 → INFO、不 FAIL', (rep & (dd.status == 'INFO')).sum() > 0 and (rep & (dd.status == 'FAIL')).sum() == 0))
    exp.append(('E6k 目录未到 → SOURCE_WAIT', ((dd.object == 'E6k') & (dd.status == 'SOURCE_WAIT')).sum() == 1))
    exp.append(('E5a 7 成员逐字节 → PASS', (dd.object.str.startswith('E5a pool') & (dd.status == 'PASS')).sum() == 7))
    rc = os.path.join(root, RN['E6'], 'roles.csv')
    R = pd.read_csv(rc)
    R.loc[0, 'worst_pooled'] = int(R.loc[0, 'worst_pooled']) + 1
    R.to_csv(rc, index=False)
    BX = Book()
    BX.out = BD.out
    a1_2(BX, root, Hasher(), refs_dir())
    dx = BX.df()
    exp.append(('roles.csv 改坏一行 → FAIL', (dx.object.str.contains('roles.csv') & dx.metric.str.contains('逐行') & (dx.status == 'FAIL')).sum() == 1))
    shutil.rmtree(fx, ignore_errors=True)
    B = Book()
    for name, ok in exp:
        B.ok('SELFTEST', 'fixture', name, True, bool(ok), bool(ok))
    return B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('task', choices=['intake', 'identity', 'close', 'selftest'])
    ap.add_argument('--out', default='')
    a = ap.parse_args()
    t0 = time.time()
    out = a.out or M.P('stage0_S')
    os.makedirs(out, exist_ok=True)
    H = Hasher()
    root = default_root()
    if a.task == 'close':
        p1, p2, gate = task_close(out)
        M.write_receipt(os.environ.get('E6M_TASK', 'S0_close'), [p1, p2], status='SUCCEEDED', code=[__file__, M.__file__], counts=gate['counts'],
                        all_pass=gate['all_pass'])
        print(json.dumps(dict(counts=gate['counts'], all_pass=gate['all_pass'], fail=gate['fail_items'], wait=gate['source_wait_items'],
                              not_run=gate['not_run_items']), ensure_ascii=False))
        return 0
    if a.task == 'intake':
        B = task_intake(root, out, H)
        p = B.write(os.path.join(out, 'intake', 'checks_intake.csv'))
    elif a.task == 'identity':
        B = task_identity(root, out, H, refs_dir())
        p = B.write(os.path.join(out, 'c1', 'checks_identity.csv'))
    else:
        B = task_selftest(out, H)
        p = B.write(os.path.join(out, 'selftest', 'checks_selftest_files.csv'))
    df = B.df()
    cnt = df.status.value_counts().to_dict()
    bad = (df.status == 'FAIL').any()
    M.write_receipt(os.environ.get('E6M_TASK', 'S0_' + a.task), [os.path.join(out, x) for x in ('intake/checks_intake.csv', 'c1/checks_identity.csv',
                                                                                                   'selftest/checks_selftest_files.csv')],
                    status='SUCCEEDED', code=[__file__, M.__file__], counts=cnt, wall_s=round(time.time() - t0, 1),
                    note='FAIL 行是检查结果（Stage 0 门在 close 汇总），不是任务失败')
    print(json.dumps(dict(task=a.task, counts=cnt, wall_s=round(time.time() - t0, 1)), ensure_ascii=False))
    show = df[df.status.isin(['FAIL', 'NOT_RUN'])]
    if len(show):
        print(show[['item', 'object', 'metric', 'expected', 'got', 'status']].head(40).to_string(max_colwidth=70))
    return 0 if (a.task != 'selftest' or not bad) else 1


if __name__ == '__main__':
    sys.exit(main())
