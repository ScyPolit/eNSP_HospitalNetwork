from configure_lab import *
for n,_,_ in INV['groups']:
    vs=[int(v) for v,d in INV['vlans'].items() if d['agg']==n and int(v) not in [60,61]]
    c=['system-view']
    for v in vs:
        c += [f'undo traffic-filter inbound acl {3000+v}',f'traffic-filter vlan {v} inbound acl {3000+v}']
    print(apply(n,c+['return'],'acl-vlan-fix'))
