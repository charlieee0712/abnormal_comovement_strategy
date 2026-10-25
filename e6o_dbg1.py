import numpy as np, e6o_core as O, e6o_engine as E, e6o_run as RU
RU.setup(); mk = RU.G['mk']; d19 = RU.d19()
P = RU.plan().set_index('exec_id', drop=False)
eid = P[(P.form == O.MAIN_FORM) & (P.memory == 'HG10') & (P.H == 5) & (P.trigger == 'T1b') & (P.fund == 'NATIVE') & (P.reentry == 'ALLOW') & (P.lag == 1) & (P.maturity == 0) & (P.family == 'CORE') & (P.ideal == 0)].exec_id.iloc[0]
acc = RU.make_account(P.loc[eid].to_dict()); acc.ip[E.IP_TLOG] = 1
acc.TL_i = np.zeros((1 << 21, 2), np.int64); acc.TL_f = np.zeros((1 << 21, 4)); acc.run(0, d19)
IN = acc.IN_i[:int(acc.S_i[E.SI_NIN])]; sok = np.asarray(mk.sellable) & np.asarray(mk.isopen)
st, ex, dd, ss = IN[:, E.IN_STATUS], IN[:, E.IN_EXEC], IN[:, E.IN_DAY], IN[:, E.IN_SEC]
bad = [i for i in np.flatnonzero((st == 1) | (st == 2)) if ex[i] > dd[i] + 1 and sok[dd[i] + 1:ex[i], ss[i]].any()]
print('bad', len(bad), 'status of bad', np.unique(st[bad], return_counts=True))
n = int(acc.S_i[E.SI_NTL]); TLi, TLf = acc.TL_i[:n], acc.TL_f[:n]
for i in bad[:6]:
    s = ss[i]; t = dd[i]; e = ex[i]
    print('intent T=%d exec=%d sec=%d status=%d qty_at_intent=%.6g' % (t, e, s, st[i], acc.IN_f[i, 1]))
    print('  sellable', [int(x) for x in np.asarray(mk.sellable)[t:e + 2, s]], 'open', [int(x) for x in np.asarray(mk.isopen)[t:e + 2, s]])
    m = (TLi[:, 1] == s) & (TLi[:, 0] >= t) & (TLi[:, 0] <= e + 1)
    for k in np.flatnonzero(m):
        print('   trade d=%d sq=%.6g bq=%.6g P=%.4f' % (TLi[k, 0], TLf[k, 0], TLf[k, 1], TLf[k, 2]))
    # 同证券其它意向
    o = np.flatnonzero((ss == s) & (dd >= t - 6) & (dd <= e))
    print('  same-sec intents', [(int(dd[j]), int(ex[j]), int(st[j])) for j in o])
