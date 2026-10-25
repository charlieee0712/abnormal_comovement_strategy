# -*- coding: utf-8 -*-
"""调试：D95 × ABS01 无退出父逐日跑，定位首个错误日并打印当日求解诊断槽（不读收益）。用法：python3 e6p_dbg1.py"""
import numpy as np

import e6p_core as O
import e6p_engine as E
import e6p_acct as A

mk = A.Market()
f = mk.formation(O.MAIN_FORM, 'HG10')
ip, fp = A.ip_fp(20, E.TM_NONE, fund=E.FD_NATIVE, deploy=E.DP_TARGET, target=0.95, cap=E.CP_ABS01)
a = A.Account(mk, ip, fp, None, f, nf_csr=mk.natural(O.MAIN_FORM))
for d in range(mk.T):
    try:
        a.run(d, d + 1)
    except RuntimeError:
        pass
    if a.S_i[E.SI_ERR] != 0:
        DY = a.DY
        print('error', int(a.S_i[E.SI_ERR]), 'day', d, mk.dates[d])
        print('need_tag %.6e ordinary0 %.6e tk_av %.6e err9 %d' % (a.S_f[4], a.S_f[5], a.S_f[6], int(a.S_f[7])))
        print('cash %.6e prev-day cash_share %.6e nav_post %.6e' % (a.S_f[E.SF_CASH], DY[d - 1, 6], DY[d - 1, 1]))
        print('zr %.6g zx %.6g zd %.6g buy %.6e sell %.6e fee %.6e deploy_plan(prev) %.6e' % (DY[d, 28], DY[d, 29], DY[d, 44], DY[d, 21], DY[d, 22], DY[d, 2], DY[d - 1, 41]))
        for k in range(max(0, d - 3), d + 1):
            print(k, 'cash_share %.3e buy %.4e sell %.4e fee %.4e zr %.4g zd %.4g dplan %.4e dbuy %.4e' % (DY[k, 6], DY[k, 21], DY[k, 22], DY[k, 2], DY[k, 28], DY[k, 44], DY[k, 41], DY[k, 42]))
        break
else:
    print('no error')
