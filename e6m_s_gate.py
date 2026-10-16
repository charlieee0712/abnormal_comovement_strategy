# -*- coding: utf-8 -*-
"""E6m 后段守卫（brief W11 / §10；plan §13；e6l_core.post_gate 同构）。阶段 S 里任何新对象在两后段（2019-2023 / 2024-2026）的
收益侧计算（账户、随机、统计、政策、bootstrap、四账户与分解）之前调用 post_gate；推导段不经此门。
范围与 E6l 不同处（决策端读法项）：E6l 把后段掩码事实也放在门后（mask_facts_post 授权后才算）；E6m 附录 B 的 Stage A 掩码层事实是
"每对象 × 母体 × 参数 × 段"、附录 C 校准要"四段分布"，且 Stage A 在 Stage B 冻结之前（brief §5 S2、plan §13.1：无收益机械事实），
所以本轮 Stage A 四段掩码事实不经此门；MDE80 / 配对 se / IC / 前向收益不是掩码事实，照旧在门后。
- 方式 A：用户在推导两段之后对两后段的一句话授权 → 执行端照原话写 registration/record_B_approved_E6m.json（原话 + 日期 + 冻结清单 sha）；
- 方式 B：registration/record_B_preauthorized_E6m.json（用户原话 + 日期 + 清单 sha；执行端不代写；两包冻结时由 e6m_s_stage_b freeze 照录
  registration/authorization_status_E6m_S.json 里的原话写出）。
两种授权文件的 freeze_sha256 都须等于当前冻结清单 sha（清单变了 = amendment，授权失效须重给）。
两种方式都还要 registration/record_B_conditions_receipt_E6m.json：all_pass（Stage 0 S 全 PASS、A1-auto 全 PASS）且
frozen_manifest_sha256 = 当前 registration/stageB_freeze_E6m.json 的 sha（冻结清单变了就拒绝）。
root 参数只给两向实测用临时目录；生产调用一律默认 M.P('registration')。"""
import os
import json

import e6m_core as M

AUTH_APPROVED = 'record_B_approved_E6m.json'
AUTH_PRE = 'record_B_preauthorized_E6m.json'
AUTH_COND = 'record_B_conditions_receipt_E6m.json'
FREEZE = 'stageB_freeze_E6m.json'


def _root(root):
    return root or M.P('registration')


def post_gate(pname, what='', root=None):
    if pname not in M.POST_SEGS:
        return True
    r0 = _root(root)
    pre, appr, rc, man = (os.path.join(r0, f) for f in (AUTH_PRE, AUTH_APPROVED, AUTH_COND, FREEZE))
    if not (os.path.exists(pre) or os.path.exists(appr)):
        raise RuntimeError('后段守卫（%s）：E6m 两后段未授权' % what)
    fsha = M.sha_file(man) if os.path.exists(man) else None
    for p in (pre, appr):
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            if not (d.get('user_quote') and d.get('user_quote_date')):
                raise RuntimeError('后段守卫（%s）：授权文件缺用户原话或日期' % what)
            if d.get('freeze_sha256') != fsha:                          # 授权绑定的冻结清单 = 当前冻结清单（amendment 使授权失效，brief W11）
                raise RuntimeError('后段守卫（%s）：授权绑定的冻结清单 sha 与当前不符（须重新授权）' % what)
    if not os.path.exists(rc):
        raise RuntimeError('后段守卫（%s）：授权生效条件未核验' % what)
    r = json.load(open(rc, encoding='utf-8'))
    if not (r.get('all_pass') and os.path.exists(man) and r.get('frozen_manifest_sha256') == M.sha_file(man)):
        raise RuntimeError('后段守卫（%s）：条件未全过或冻结清单 sha 已变' % what)
    return True


def deriv_only(pname, what=''):
    if pname not in M.DERIV_SEGS:
        raise RuntimeError('%s：本步只允许推导段' % what)
    return True


def two_way(tmp):
    """A1-3（S）post_gate 两向实测：临时目录里伪造文件，只写 tmp。返回逐例 dict。"""
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
    fz = lambda: M.sha_file(os.path.join(tmp, FREEZE))
    put(AUTH_APPROVED, {'mode': 'A', 'freeze_sha256': fz()})
    case('方式 A 授权缺用户原话 → 拒绝', False)
    put(AUTH_APPROVED, {'mode': 'A', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-05', 'freeze_sha256': fz()})
    case('有授权、缺条件回执 → 拒绝', False)
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    case('授权 + 条件全过 + 清单 sha 相同 → 放行', True)
    put(FREEZE, {'x': 2})
    case('清单 sha 已变 → 拒绝', False)
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    case('条件回执跟新清单、授权仍绑旧清单 → 拒绝（amendment 须重新授权）', False)
    put(AUTH_APPROVED, {'mode': 'A', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-05', 'freeze_sha256': fz()})
    put(AUTH_COND, dict(all_pass=False, frozen_manifest_sha256=fz()))
    case('条件未全过 → 拒绝', False)
    os.remove(os.path.join(tmp, AUTH_APPROVED))
    put(AUTH_PRE, {'mode': 'B', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-05', 'freeze_sha256': fz()})
    put(AUTH_COND, dict(all_pass=True, frozen_manifest_sha256=fz()))
    case('方式 B 事前授权 + 条件全过 → 放行', True)
    put(AUTH_PRE, {'mode': 'B', 'user_quote': '（两向实测伪造）', 'user_quote_date': '2026-10-05'})
    case('方式 B 授权未绑清单 sha → 拒绝', False)
    try:
        deriv_only('2024-2026', 'two-way')
        rows.append(dict(case='deriv_only 后段 → 拒绝', expect='RAISE', got='PASS', ok=False))
    except RuntimeError as e:
        rows.append(dict(case='deriv_only 后段 → 拒绝', expect='RAISE', got='RAISE ' + str(e)[:60], ok=True))
    shutil.rmtree(tmp)
    return rows
