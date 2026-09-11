#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E6g 描述符构建: 扩展 e6f_blockA_lib.Ctx 以支持
   任意注册键作腿 (role 'F') / 逐腿方向 / 逐腿变换 / 三个具名 selector / 有理权重四腿核。

不改 e6f_*.py。默认参数下【直接委托】给 e6f 的 Ctx.build_core, 因此 OLD 域逐位相同
—— 不是"应该相同", 是同一段代码。
"""
import sys, copy
from fractions import Fraction
import numpy as np
import pandas as pd

sys.path.insert(0, '/mnt/sda2/lichenchen/code/project_core')
import e6e_core as K
import e6f_core as F
import e6f_desc as D
import e6f_blockA_lib as A
import e6g_core as G

DEF = D.DEF                       # role -> 默认规格
ROLE_OF_KEY = {K.FK: 'K', K.FT: 'T', K.FC: 'C', K.FCVR1: 'Cf', K.FCR5: 'B', K.FCR20: 'B'}


def spec_of_key(key):
    """已有 E6f 角色的键沿用原规格 (保持 cfg_id 与锚不变); 其余走 role 'F'。"""
    if key == K.FK:
        return dict(D.DK)
    if key == K.FT:
        return dict(D.DT_)
    if key == K.FC:
        return dict(D.DC)
    if key == K.FCVR1:
        return dict(D.DCF)
    if key == K.FCR5:
        return dict(D.DB5)
    if key == K.FCR20:
        return dict(D.DB20)
    return G.specF(key)


def short_of_key(key):
    sp = spec_of_key(key)
    return D.VSHORT(sp) if sp.get('role') != 'F' else key


# ---------------------------------------------------------------- 名字 -> 配置
_CORE_PAT = None


_EPS = {'1e-5': 1e-5, '1e-4': 1e-4, '1e-3': 1e-3}


def parse_fid(s):
    """F.fid 的逆: 'T40' / 'C20' / 'KMA3@1e-4' / 'Cf1r' / 'B5u' -> 规格 dict。
       让 E6e / E6f 的任意描述符都能重建 (B1 的政策账户要真的重跑批次)。"""
    import re
    m = re.match(r'^T(\d+)$', s)
    if m:
        return F.spec('T', int(m.group(1)))
    m = re.match(r'^C(\d+)$', s)
    if m:
        return F.spec('C', int(m.group(1)))
    m = re.match(r'^K(MA|ROS)(\d+)@(\S+)$', s)
    if m:
        return F.spec('K', int(m.group(2)), est=m.group(1),
                      eps=_EPS.get(m.group(3), float(m.group(3))))
    m = re.match(r'^Cf(\d+)([rd])$', s)
    if m:
        return F.spec('Cf', int(m.group(1)), base=('ratio' if m.group(2) == 'r' else 'diff'))
    m = re.match(r'^B(\d+)([au])$', s)
    if m:
        return F.spec('B', int(m.group(1)), adj=(m.group(2) == 'a'))
    m = re.match(r'^F:(.+?)(?:@MA(\d+))?$', s)
    if m:
        return G.specF(m.group(1), int(m.group(2)) if m.group(2) else 1)
    return None


def parse_core(name):
    """'KTC_mean@25' / 'KT_dep(50,50)' / 'T@30' / 'KTC_mean@35{KMA3@1e-4,T20}' -> core dict。
       花括号块按角色回填到对应腿位 (均值核按 MEANF 的角色顺序; DEP 核按 x / ys)。"""
    import re
    tag = ''
    m = re.match(r'^(.*?)\{(.*)\}$', name)
    if m:
        name, tag = m.group(1), m.group(2)
    m = re.match(r'^([A-Za-z_]+)@(\d+(?:\.\d+)?)$', name)
    if m:
        s_ = m.group(2)
        core = D.default_core(m.group(1), s=(float(s_) if '.' in s_ else int(s_)))
    else:
        m = re.match(r'^([A-Za-z_]+)\((\d+),(\d+)\)$', name)
        if not m:
            raise ValueError('无法解析核名 %r' % (name,))
        core = D.default_core(m.group(1), a=int(m.group(2)), b=int(m.group(3)))
    if not tag:
        return core
    core = copy.deepcopy(core)
    # e6g core_id_g 的有序腿表形式: {legs:K^lo.delta5=1/8,T60,C20;neu:NI}
    if tag.startswith('legs:') or tag.startswith('x:'):
        comps, dirs, tfs, ws = [], [], [], []
        for blk in tag.split(';'):
            blk = blk.strip()
            if blk.startswith('legs:'):
                for leg in blk[5:].split(','):
                    w_ = None
                    if '=' in leg:
                        leg, w_ = leg.rsplit('=', 1)
                    tf_ = 'identity'
                    if '.' in leg and not re.search(r'@\d*\.', leg):
                        leg, tf_ = leg.rsplit('.', 1)
                    dr_ = 'hi'
                    if '^' in leg:
                        leg, dr_ = leg.rsplit('^', 1)
                    sp = parse_fid(leg.strip())
                    if sp is None:
                        raise ValueError('腿表里无法解析 %r' % leg)
                    comps.append(sp); dirs.append(dr_); tfs.append(tf_)
                    ws.append(Fraction(w_) if w_ else None)
            elif blk.startswith('x:'):
                core['x'] = parse_fid(blk[2:].strip())
            elif blk.startswith('y:'):
                core['ys'] = [parse_fid(y.strip()) for y in blk[2:].split(',') if y.strip()]
            elif blk.startswith('neu:'):
                core['neu'] = blk[4:]
            elif blk.startswith('vneu:'):
                core['neu_veto'] = blk[5:]
        if comps:
            core['comps'] = comps
            core['dirs'] = dirs
            core['tfs'] = tfs
            core['ws'] = ws if all(w is not None for w in ws) else None
        return core
    for part in re.split(r',(?![^@]*\))', tag):
        part = part.strip()
        if not part:
            continue
        if part.startswith('w'):
            # 注意: 这里【不能】再写 from fractions import Fraction —— 函数里出现局部导入
            # 会把整个函数作用域里的 Fraction 变成局部名, 上面 legs: 分支就会
            # UnboundLocalError。模块顶部已经 import 过。
            core['ws'] = [Fraction(x) for x in part[1:].split('/') if x]
            continue
        if part.startswith('neu:'):
            core['neu'] = part[4:]; continue
        if part.startswith('vneu:'):
            core['neu_veto'] = part[5:]; continue
        sp = parse_fid(part)
        if sp is None:
            raise ValueError('花括号里无法解析的规格 %r (核 %r)' % (part, name))
        r = sp.get('role')
        placed = False
        for i, c0 in enumerate(core.get('comps') or []):
            if c0.get('role') == r:
                core['comps'][i] = sp; placed = True; break
        if not placed and core.get('x') and core['x'].get('role') == r:
            core['x'] = sp; placed = True
        if not placed:
            for i, y in enumerate(core.get('ys') or []):
                if y.get('role') == r:
                    core['ys'][i] = sp; placed = True; break
        if not placed:
            raise ValueError('规格 %r 在核 %r 里没有对应腿位' % (part, name))
    return core


_VSHORT2SPEC = {'C': D.DC, 'cvr_1d': D.DCF, 'cr5': D.DB5, 'cr20': D.DB20,
                'K': D.DK, 'T': D.DT_}


def parse_veto(name):
    """'C:k5+cr5:k10' / 'cmp_mean(cvr_1d,cr5):k10' / '' -> e6f veto dict 或 None。"""
    import re
    if not name:
        return None
    m = re.match(r'^cmp_(\w+)\(([^)]*)\):k(\d+)$', name)
    if m:
        how, legs, k = m.group(1), m.group(2).split(','), int(m.group(3))
        return dict(vid=name, kind='composite', how=how, k=k,
                    legs=[(dict(_VSHORT2SPEC[x.strip()]), k) for x in legs])
    legs = []
    for part in name.split('+'):
        nm, kk = part.rsplit(':k', 1)
        sp = _VSHORT2SPEC.get(nm)
        if sp is None:
            sp = spec_of_key(nm)
        legs.append((dict(sp), int(kk)))
    return D.veto_hard(legs, vid=name)


def parse_cfg(cfg_id):
    """'KTC_mean@25|cvr_1d:k10+cr5:k10[~sel:QEDGE][~tf:...][~dir:lo]...' -> 可执行 cfg。
       E6g 的 '~' 后缀块要先摘下来再解析核/否决, 并把 sel / tf / dir 回填到核上。"""
    body = cfg_id
    suf = {}
    if '~' in body:
        bits = body.split('~')
        body = bits[0]
        for b in bits[1:]:
            if ':' in b:
                k_, v_ = b.split(':', 1)
                suf[k_] = v_
    H = K.HOLD
    if '@H' in body:
        body, hh = body.rsplit('@H', 1)
        H = int(hh.split('#')[0])
    sup = 'legacy_all'
    if '#' in body:
        body, sup = body.rsplit('#', 1)
    parts = body.split('|')
    core = parse_core(parts[0])
    veto = parse_veto(parts[1]) if len(parts) > 1 and parts[1] else None
    if suf.get('sel'):
        core['sel'] = suf['sel']
        if suf['sel'] == 'RANKBUDGET':
            core['depth'] = core.get('s') if core['kind'] in ('single', 'mean') else core.get('b')
    # 【修正 F7, 交付后】~tf: / ~dir: 是「全腿同值」的简写後缀; 但当核心带 {legs:...}
    # 花括号块时 parse_core 已经逐腿解出 tfs/dirs, 后缀会把逐腿值抹平成全 lo/全同变换。
    # 花括号块更具体, 优先; 后缀只在核心没给逐腿值时兜底。
    # (核查: B/B1_paths_EXPANDED.json 的 86 个被选配置里 ~dir:lo 出现 0 次,
    #  本轮所有已交付数字不受影响 —— 这是给下一轮的潜在缺陷修复。)
    if suf.get('tf') and not core.get('tfs'):
        n = len(core.get('comps') or []) or 1
        core['tfs'] = [suf['tf']] * n
    if suf.get('dir') == 'lo' and not core.get('dirs'):
        n = len(core.get('comps') or []) or 1
        core['dirs'] = ['lo'] * n
    return dict(config_id=cfg_id, core=core, veto=veto, H=H, support=sup)


def display_configs():
    """固定展示组 (plan §1.3)。返回 [(label, cfg)]。"""
    return [(lab, parse_cfg(cid)) for lab, cid, _ in G.DISPLAY]


# ---------------------------------------------------------------- 扩展核
def mk_core_g(fam, kind, s=None, a=None, b=None, keys=(), ws=None, neu='NS',
              dirs=None, tfs=None, sel='SRC', depth=None, x_key=None, y_keys=()):
    """任意键作腿的核。keys / x_key / y_keys 用【注册键名】, 内部转规格。"""
    comps = [spec_of_key(k) for k in keys]
    c = dict(fam=fam, kind=kind, s=s, a=a, b=b, comps=comps,
             x=(spec_of_key(x_key) if x_key else None),
             ys=[spec_of_key(k) for k in y_keys], ws=ws, neu=neu, neu_veto=None)
    c['dirs'] = list(dirs) if dirs else ['hi'] * max(1, len(comps))
    c['tfs'] = list(tfs) if tfs else ['identity'] * max(1, len(comps))
    c['sel'] = sel
    c['depth'] = depth
    return c


def _canon_legs_of(fam):
    """E6f 家族的规范腿顺序 —— 用来判断一个核是不是"原样"的。"""
    if fam in D.MEANF:
        return [D.DEF[r] for r in D.MEANF[fam]]
    if fam in D.SINGLE:
        return [D.DEF[D.SINGLE[fam]]]
    return None


def _is_e6f_shape(c):
    """腿的【身份与位置】都还是 E6f 家族原样 (只有窗口/eps 可以不同), 且无方向/变换改动。"""
    if any(d != 'hi' for d in (c.get('dirs') or [])):
        return False
    if any(t != 'identity' for t in (c.get('tfs') or [])):
        return False
    can = _canon_legs_of(c['fam'])
    comps = c.get('comps') or []
    if c['kind'] == 'dep':
        return all(sp.get('role') != 'F' for sp in
                   ([c['x']] if c.get('x') else []) + (c.get('ys') or []))
    if can is None or len(can) != len(comps):
        return False
    return all(sp.get('role') == ref['role'] for sp, ref in zip(comps, can))


def core_id_g(c):
    """核的规范 ID。【E6f 原样时逐字等于 e6f_desc.core_id】, 因此 OLD 域的 cfg_id 不变。

       一旦腿的身份 / 位置 / 方向 / 变换被动过 (换腿、第四腿、H2 变换), 就必须把
       【有序腿表】整个写进 ID —— 否则 "K 位换成 J" 与 "T 位换成 J" 会撞成同一个名字
       (实测 H1 的 1,544 个描述符会塌成 992 个)。"""
    if _is_e6f_shape(c):
        return D.core_id(c)
    dirs = c.get('dirs') or ['hi'] * len(c.get('comps') or [])
    tfs = c.get('tfs') or ['identity'] * len(c.get('comps') or [])
    ws = c.get('ws')
    legs = []
    for i, sp in enumerate(c.get('comps') or []):
        t = G.fidg(sp)
        if i < len(dirs) and dirs[i] != 'hi':
            t += '^' + dirs[i]
        if i < len(tfs) and tfs[i] != 'identity':
            t += '.' + tfs[i]
        if ws is not None:
            t += '=' + str(ws[i])
        legs.append(t)
    parts = ['legs:' + ','.join(legs)] if legs else []
    if c['kind'] == 'dep':
        parts = ['x:' + G.fidg(c['x']),
                 'y:' + ','.join(G.fidg(y) for y in (c.get('ys') or []))]
    if c.get('neu', 'NS') != 'NS':
        parts.append('neu:' + c['neu'])
    if c.get('neu_veto') is not None and c['neu_veto'] != c.get('neu', 'NS'):
        parts.append('vneu:' + c['neu_veto'])
    tag = ('{' + ';'.join(parts) + '}') if parts else ''
    if c['kind'] in ('single', 'mean'):
        s = c['s']
        return '%s@%s%s' % (c['fam'], ('%g' % s) if isinstance(s, float) else s, tag)
    return '%s(%s,%s)%s' % (c['fam'], c['a'], c['b'], tag)


def cfg_id_g(core, veto, H=K.HOLD, sup='legacy_all', sel='SRC', dirs=None, tfs=None,
             buf=None, tie='src', state=None):
    """E6g 描述符 ID。全部默认 -> 逐字等于 e6f_desc.cfg_id。"""
    s = core_id_g(core)
    if veto:
        s += '|' + veto['vid']
    if H != K.HOLD:
        s += '@H%d' % H
    if sup != 'legacy_all':
        s += '#' + sup
    dirs = dirs if dirs is not None else (core.get('dirs') or [])
    tfs = tfs if tfs is not None else (core.get('tfs') or [])
    dr = 'lo' if any(d == 'lo' for d in dirs) else 'hi'
    tf = next((t for t in tfs if t != 'identity'), 'identity')
    alpha = None
    if core.get('ws') is not None and len(core['ws']) >= 4:
        alpha = core['ws'][-1]
    return G.gid(s, sel=(sel if sel != 'SRC' else core.get('sel', 'SRC')), tf=tf, dr=dr,
                 alpha=(float(alpha) if alpha is not None else None), buf=buf, tie=tie,
                 state=state)


def path_fields(core, veto, H=K.HOLD, sup='legacy_all', sel=None, buf=None, tie='src',
                state=None, seed=None):
    """真实计算路径的字段包 (喂给 G.path_key)。腿序与否决腿序都规范化。"""
    legs = [G.fidg(sp) for sp in (core.get('comps') or [])]
    ws = [str(x) for x in (core.get('ws') or [])] or None
    dirs = core.get('dirs') or ['hi'] * len(legs)
    tfs = core.get('tfs') or ['identity'] * len(legs)
    legs2 = ['%s~%s~%s' % (a, b, c) for a, b, c in zip(legs, dirs, tfs)]
    if core['kind'] == 'dep':
        core_s = '%s(%s,%s):x=%s:y=%s' % (core['fam'], core['a'], core['b'],
                                          G.fidg(core['x']),
                                          G.canon_legs([G.fidg(y) for y in core['ys']]))
    else:
        core_s = '%s@%s:%s' % (core['fam'], core['s'], G.canon_legs(legs2, ws))
    return dict(core=core_s, veto=(veto or {}).get('vid'), H=H, support=sup,
                sel=(sel or core.get('sel', 'SRC')), tf=None, dr=None, alpha=None,
                buf=buf, tie=tie, state=state, neu=core.get('neu', 'NS'), seed=seed,
                selector_veto=(sel or core.get('sel', 'SRC')))


def _is_plain(core):
    """能否直接委托给 e6f 的 Ctx.build_core (= OLD 域逐位相同)。"""
    if core.get('sel', 'SRC') != 'SRC':
        return False
    if core.get('depth') is not None:
        return False
    if not _is_e6f_shape(core):          # 换腿 / 第四腿 / 四腿聚合族一律走本模块
        return False
    if any(d != 'hi' for d in core.get('dirs', []) or []):
        return False
    if any(t != 'identity' for t in core.get('tfs', []) or []):
        return False
    for sp in (core.get('comps') or []) + ([core['x']] if core.get('x') else []) + \
              (core.get('ys') or []):
        if sp.get('role') == 'F':
            return False
    return True


def core_lineage(core):
    lin = G.Lin()
    for sp in (core.get('comps') or []) + ([core['x']] if core.get('x') else []) + \
              (core.get('ys') or []):
        lin = lin | G.lin_of_spec(sp)
    return lin


def veto_lineage(veto):
    lin = G.Lin()
    if veto:
        for sp, _ in veto['legs']:
            lin = lin | G.lin_of_spec(sp)
    return lin


class GCtx(A.Ctx):
    """E6g 上下文。默认参数一律走父类。"""

    def __init__(self, S, lru=None):
        A.Ctx.__init__(self, S) if lru is None else A.Ctx.__init__(self, S, lru)
        self._gcc = {}
        self.report = {}

    # ---- 腿的 pct 表 ----
    def leg_pct(self, sp, md='NS', direction='hi', transform='identity'):
        G.assert_registered_spec(sp, 'GCtx.leg_pct')
        if sp.get('role') != 'F' and direction == 'hi' and transform == 'identity':
            return F.get_pct(self.S, sp, md)          # 与 E6f 同一条代码路径
        return G.get_pct_g(self.S, sp, md, direction, transform)

    # ---- selector ----
    def _keep(self, score, pool, depth_pct, sel, depth=None):
        if sel == 'SRC':
            return G.keep_SRC(score, pool, depth_pct)
        if sel == 'QEDGE':
            return G.keep_QEDGE(score, pool, depth_pct, report=self.report)
        if sel == 'RANKBUDGET':
            return G.keep_RANKBUDGET(score, pool, depth if depth is not None else depth_pct,
                                     report=self.report)
        raise ValueError(sel)

    # ---- 核 ----
    def build_core_g(self, core, pool_override=None):
        if _is_plain(core):
            return A.Ctx.build_core(self, core, pool_override)
        S = self.S
        md = core.get('neu', 'NS') or 'NS'
        sel = core.get('sel', 'SRC')
        dep = core.get('depth')
        p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
        dirs = core.get('dirs') or ['hi'] * len(core.get('comps') or [])
        tfs = core.get('tfs') or ['identity'] * len(core.get('comps') or [])
        if core['kind'] in ('single', 'mean'):
            Ps = [self.leg_pct(sp, md, dirs[i] if i < len(dirs) else 'hi',
                               tfs[i] if i < len(tfs) else 'identity')
                  for i, sp in enumerate(core['comps'])]
            ws = core.get('ws')
            if ws is not None:
                wf = [float(x) for x in ws]
                score = F.wcombine_dense(Ps, wf)
                used = [Pi for Pi, w in zip(Ps, wf) if w > 0]
                if core['fam'].startswith('KTC') and len(used) > 1:
                    score = np.where(F.common_domain(used), score, np.nan)
            elif core['fam'].startswith('KTC4_'):
                score = G.agg_dense(Ps, core['fam'].split('_', 1)[1])   # 四腿聚合 (H5)
            elif len(Ps) == 1:
                score = Ps[0]
            else:
                score = F.combine_dense(Ps, 'mean',
                                        complete=core['fam'].startswith('KTC'))
            m = self._keep(score, p0, core['s'], sel, dep)
            return m, score, p0
        # 两段式
        Px = self.leg_pct(core['x'], md, (dirs[0] if dirs else 'hi'),
                          (tfs[0] if tfs else 'identity'))
        # 【登记的实现决定】第一阶段闸一律走 SRC (brief §5 H4-a: "K 第一阶段固定 50%"),
        # selector 只作用于第二阶段。否则 RANKBUDGET 会把 50% 的 P2G[50]=2 组闸
        # 换成 floor(n*0.5), 改的就不再是"经济深度"这一个杠杆了。
        s1 = self._keep(Px, p0, core['a'], 'SRC')
        S1full = np.zeros((S.T, S.Nfull))
        S1full[:, S.ccols] = s1.astype(float)
        S1df = pd.DataFrame(S1full, index=S.pool0.index, columns=S.pool0.columns)
        parts = []
        for y in core['ys']:
            raw = G.build_raw_g(S, y)
            if raw.shape != S.pool0.shape or not raw.index.equals(S.pool0.index):
                raw = raw.reindex(index=S.pool0.index, columns=S.pool0.columns)
            cch, _ = F.neu_cache(raw, S1df, S.log_mcap, S.icodes_neu, md)
            parts.append(G.pct_dense_dir(cch, S.dates, S.ccolpos, S.Nc, 'hi'))
        score = parts[0] if len(parts) == 1 else F.combine_dense(parts, 'mean')
        m = self._keep(score, s1, core['b'], sel, dep)
        return m, score, s1

    # ---- 否决 ----
    def build_veto_drop_g(self, veto, core, pool_override=None, sel='SRC'):
        if not veto:
            return None
        if sel == 'SRC' and all(sp.get('role') != 'F' for sp, _ in veto['legs']):
            return A.Ctx.build_veto_drop(self, veto, core, pool_override)
        S = self.S
        md = core.get('neu_veto') or core.get('neu', 'NS') or 'NS'
        p0 = S.p0c if pool_override is None else (S.p0c & pool_override)
        dropf = (G.drop_SRC if sel == 'SRC'
                 else (lambda P, pp, kk: G.drop_QEDGE(P, pp, kk, report=self.report)))
        if veto['kind'] == 'composite':
            Ps = [self.leg_pct(sp, md, veto.get('dir', 'hi'),
                               veto.get('tf', 'identity')) for sp, _ in veto['legs']]
            comp = F.combine_dense(Ps, veto['how'], complete=True)
            return dropf(comp, p0, veto['k'])
        dr = np.zeros_like(p0)
        for sp, k in veto['legs']:
            dr |= dropf(self.leg_pct(sp, md, veto.get('dir', 'hi'),
                                     veto.get('tf', 'identity')), p0, k)
        return dr

    def full_mask_g(self, cfg, pool_override=None):
        core = cfg['core']
        sel = core.get('sel', 'SRC')
        m, sc, cand = self.build_core_g(core, pool_override)
        dr = self.build_veto_drop_g(cfg.get('veto'), core, pool_override,
                                    sel=('QEDGE' if sel == 'QEDGE' else 'SRC'))
        return ((m & ~dr) if dr is not None else m), sc, cand, m

    def lineage(self, cfg):
        return core_lineage(cfg['core']) | veto_lineage(cfg.get('veto'))

    def run(self, cfg, pool_override=None, H=None, cost_bp=F.COST, use_type='trade'):
        """掩码 -> DEV -> 引擎。带 40 键守卫。"""
        G.guard(self.lineage(cfg), use_type, segment=self.S.name,
                label_end=cfg.get('label_end'), where=cfg.get('config_id', '?'))
        mk = self.full_mask_g(cfg, pool_override)[0]
        idx, val = F.dev_from_dense(self.S, mk)
        pnl = F.sparse_pnl_H(self.S, idx, val, H or cfg.get('H', K.HOLD), cost_bp)
        return pnl, (idx, val), mk


def interior_nopos(pos):
    """段内零仓位日 = 全部零仓位日 - 段首连续零仓位段 (E6f_REVIEW §1.3 的标准列)。"""
    z = (~np.isfinite(pos)) | (pos == 0.0)
    if not z[0]:
        lead = 0
    else:
        nz = np.flatnonzero(~z)
        lead = int(nz[0]) if len(nz) else int(len(z))
    return int(z.sum() - lead), lead
