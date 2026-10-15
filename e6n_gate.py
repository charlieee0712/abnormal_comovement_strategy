# -*- coding: utf-8 -*-
"""E6n 后段守卫与授权文件（brief W10、A3、A10；e6m_s_gate 同构）。两后段（2019-2023 / 2024-2026）任何收益侧计算（账户、随机、统计、政策、
bootstrap、四账户与分解、B2–B6 的后段部分）之前调用 post_gate；推导段不经此门。
放行条件（W10 方式 B）：registration/record_B_preauthorized_E6n.json（用户原话 + 日期 + 绑定冻结清单 sha）或方式 A 批准文件；
registration/record_B_conditions_receipt_E6n.json：all_pass（Stage 0 全 PASS、A1-auto 全 PASS、B1-0 已封存、seal_deriv 已写）且
frozen_manifest_sha256 = 当前 registration/stageB_freeze_E6n.json 的 sha；registration/seal_B1_0.json 与 seal_deriv.json 都在。
授权文件只照录用户原话（执行端不代拟）；清单变了 = amendment，授权失效须重给。root 只给两向实测用临时目录。"""
import os
import json

import e6n_core as N

AUTH_STATUS = 'authorization_status_E6n.json'
AUTH_APPROVED = 'record_B_approved_E6n.json'
AUTH_PRE = 'record_B_preauthorized_E6n.json'
AUTH_COND = 'record_B_conditions_receipt_E6n.json'
FREEZE = 'stageB_freeze_E6n.json'
SEAL_B10 = 'seal_B1_0.json'
SEAL_DERIV = 'seal_deriv.json'
USER_QUOTE = '选项B 记得好好思考执行过程优化方案 中途不用done停下来汇报'


def _root(root):
    return root or N.P('registration')


def post_gate(pname, what='', root=None):
    if pname not in N.POST_SEGS:
        return True
    r0 = _root(root)
    pre, appr, rc, man, s10, sd = (os.path.join(r0, f) for f in (AUTH_PRE, AUTH_APPROVED, AUTH_COND, FREEZE, SEAL_B10, SEAL_DERIV))
    if not (os.path.exists(pre) or os.path.exists(appr)):
        raise RuntimeError('后段守卫（%s）：E6n 两后段未授权' % what)
    fsha = N.sha_file(man) if os.path.exists(man) else None
    for p in (pre, appr):
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            if not (d.get('user_quote') and d.get('user_quote_date')):
                raise RuntimeError('后段守卫（%s）：授权文件缺用户原话或日期' % what)
            if d.get('freeze_sha256') != fsha:
                raise RuntimeError('后段守卫（%s）：授权绑定的冻结清单 sha 与当前不符（须重新授权）' % what)
    for p, nm in ((s10, 'seal_B1_0'), (sd, 'seal_deriv')):
        if not os.path.exists(p):
            raise RuntimeError('后段守卫（%s）：%s 未写' % (what, nm))
    if not os.path.exists(rc):
        raise RuntimeError('后段守卫（%s）：授权生效条件未核验' % what)
    r = json.load(open(rc, encoding='utf-8'))
    if not (r.get('all_pass') and os.path.exists(man) and r.get('frozen_manifest_sha256') == N.sha_file(man)):
        raise RuntimeError('后段守卫（%s）：条件未全过或冻结清单 sha 已变' % what)
    return True


def deriv_only(pname, what=''):
    if pname not in N.DERIV_SEGS:
        raise RuntimeError('%s：本步只允许推导段' % what)
    return True


def deriv_ready(pname, what='', root=None):
    """推导段读收益（账户 / 随机 / 统计）之前：Stage B 冻结清单与 seal_B1_0 都已写（brief §1.4 / A3：B1-0 封存先于任何推导段账户；闭包门 ⑦）。
    后段另走 post_gate。"""
    if pname in N.POST_SEGS:
        return post_gate(pname, what, root=root)
    r0 = _root(root)
    for f, nm in ((FREEZE, 'Stage B 冻结清单'), (SEAL_B10, 'seal_B1_0')):
        if not os.path.exists(os.path.join(r0, f)):
            raise RuntimeError('推导段守卫（%s）：%s 未写' % (what, nm))
    return True


def write_status():
    """开工时照录用户转交消息原话（方式 B 的依据）；不是授权文件本身（授权文件在冻结时绑清单 sha 写出）。"""
    p = N.P('registration', AUTH_STATUS)
    N.atomic_write_json(p, dict(w10_mode='B', user_quote=USER_QUOTE, user_quote_date='2026-10-15（47 时间 CST；本机 EDT 10-14 晚）',
                                basis='brief W10：转交消息含 "B" → 方式 B；Stage A / B 两包冻结时写 record_B_preauthorized_E6n.json，生效条件 = Stage 0 全 PASS + '
                                      'A1-auto 全 PASS + B1-0 已封存 + 进入后段时清单 sha 不变',
                                not_reused=['E6m / E6l 授权回执', '文件名里的 B', '写 plan / brief 的请求']))
    return p


def two_way(tmp):
    """A1-3 post_gate 两向实测：临时目录里伪造文件，只写 tmp。"""
    import shutil
    if os.path.exists(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)
    rows = []

    def case(name, expect_pass, seg='2019-2023'):
        try:
            post_gate(seg, 'two-way ' + name, root=tmp)
            got = 'PASS'
        except RuntimeError as e:
            got = 'RAISE ' + str(e)[:60]
        rows.append(dict(case=name, expect='PASS' if expect_pass else 'RAISE', got=got, ok=(got == 'PASS') == expect_pass))

    def put(name, obj):
        with open(os.path.join(tmp, name), 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False)
    case('无授权文件 → 拒绝', False)
    case('推导段不拦', True, seg='2010-2014')
    put(FREEZE, {'x': 1})
    fz = lambda: N.sha_file(os.path.join(tmp, FREEZE))
    put(AUTH_PRE, {'mode': 'B', 'freeze_sha256': fz()})
    case('方式 B 授权缺用户原话 → 拒绝', False)
    put(AUTH_PRE, {'mode': 'B', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-15', 'freeze_sha256': fz()})
    case('有授权、缺 seal_B1_0 / seal_deriv → 拒绝', False)
    put(SEAL_B10, {'written_at': 'x'})
    case('有授权 + seal_B1_0、缺 seal_deriv → 拒绝', False)
    put(SEAL_DERIV, {'written_at': 'x'})
    case('有授权 + 两封存、缺条件回执 → 拒绝', False)
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    case('授权 + 两封存 + 条件全过 + 清单 sha 相同 → 放行', True)
    put(FREEZE, {'x': 2})
    case('清单 sha 已变 → 拒绝', False)
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    case('条件回执跟新清单、授权仍绑旧清单 → 拒绝（amendment 须重新授权）', False)
    put(AUTH_PRE, {'mode': 'B', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-15', 'freeze_sha256': fz()})
    put(AUTH_COND, dict(all_pass=False, frozen_manifest_sha256=fz()))
    case('条件未全过 → 拒绝', False)
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    os.remove(os.path.join(tmp, SEAL_B10))
    case('B1-0 未封存 → 拒绝', False)
    try:
        deriv_only('2024-2026', 'two-way')
        rows.append(dict(case='deriv_only 后段 → 拒绝', expect='RAISE', got='PASS', ok=False))
    except RuntimeError as e:
        rows.append(dict(case='deriv_only 后段 → 拒绝', expect='RAISE', got='RAISE ' + str(e)[:60], ok=True))
    shutil.rmtree(tmp)
    return rows
