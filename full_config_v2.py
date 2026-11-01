from configure_lab import *
from secure_lab import agg_acls
def firewall(n,i):
    c=configs()[n]
    # Remove factory membership of GE0/0/0 from trust before assigning untrust.
    idx=c.index('firewall zone trust');c[idx:idx]=['firewall zone trust','undo add interface GigabitEthernet0/0/0','quit']
    c=c[:-1]+['firewall zone untrust','undo add interface GigabitEthernet0/0/1','quit','firewall zone name isp2','set priority 10','add interface GigabitEthernet0/0/1','quit',
       'ip service-set OSPF type object','service protocol 89','quit']
    def pol(z1,z2,dr,num,src=None,dst=None,service=None):
        c.extend([f'policy interzone {z1} {z2} {dr}',f'policy {num}'])
        if src:c.append('policy source '+src)
        if dst:c.append('policy destination '+dst)
        if service:c.append('policy service service-set '+service)
        c.extend(['action permit','quit','quit'])
    for z in ['untrust','isp2']:pol('trust',z,'outbound',1,'10.162.0.0 0.0.255.255')
    pol('dmz','untrust','inbound',1,None,'10.162.108.10 0','http')
    pol('trust','medical','outbound',1,'10.162.121.0 0.0.0.255','172.20.1.0 0.0.0.255')
    for num,dst,service in [(1,'10.162.106.10 0','https'),(2,'10.162.106.10 0','icmp'),(3,'10.162.121.10 0',None)]:pol('trust','medical','inbound',num,'172.20.1.10 0',dst,service)
    pol('trust','dmz','inbound',1,'10.162.108.10 0','10.162.106.10 0','https')
    pol('trust','dmz','outbound',1,'10.162.0.0 0.0.255.255','10.162.108.10 0','http')
    for dr in ['inbound','outbound']:
        pol('local','trust',dr,1,None,None,'OSPF');pol('local','trust',dr,2,None,None,'icmp')
        pol('local','ha',dr,1)
    lo,hi=(10,19) if i==0 else (20,30)
    c += [f'nat address-group 1 12.1.1.{lo} 12.1.1.{hi}',f'nat address-group 2 13.1.1.{lo} 13.1.1.{hi}']
    for z,k in [('untrust',1),('isp2',2)]:c += [f'nat-policy interzone trust {z} outbound','policy 1','policy source 10.162.0.0 0.0.255.255','action source-nat',f'address-group {k}','quit','quit']
    if i==0:c+=['nat server 1 protocol tcp global 12.1.1.100 80 inside 10.162.108.10 80']
    else:c+=['nat server 1 protocol tcp global 12.1.1.101 80 inside 10.162.108.10 80']
    for p,vip in [(0,'12.1.1.1'),(1,'13.1.1.1'),(2,'192.0.2.1'),(3,'10.162.99.1'),(4,'10.162.99.33'),(5,'10.162.108.1')]:c += [f'interface GigabitEthernet0/0/{p}',f'vrrp vrid {p+1} virtual-ip {vip} '+('master' if i==0 else 'slave'),'quit']
    c += ['undo hrp auto-sync config','hrp interface GigabitEthernet0/0/6','hrp ospf-cost adjust-enable','ospf 1','default-route-advertise type 1','quit','ip route-static 203.0.114.0 24 13.1.1.254',
          'user-interface console 0','screen-length 0','quit','hrp enable','return']
    return c
def aclclean(n):
    c=['system-view']
    for v,d in INV['vlans'].items():
        if d['agg']!=n or int(v) in [60,61]:continue
        c += [f'undo traffic-filter inbound acl {3000+int(v)}',f'undo traffic-filter vlan {v} inbound acl {3000+int(v)}',f'undo acl {3000+int(v)}']
    c+=['return']+agg_acls(n)
    # This simulator only supports the VLAN form of the binding.
    r=[];current=None
    for x in c:
        if x.startswith('interface Vlanif'):current=x.removeprefix('interface Vlanif')
        if x.startswith('traffic-filter inbound acl '):r += ['quit',f'traffic-filter vlan {current} inbound acl '+x.split()[-1]]
        else:r.append(x)
    return r
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fw',action='store_true');ap.add_argument('--acl',action='store_true');ap.add_argument('--base',action='store_true');a=ap.parse_args();cc={}
    if a.base:cc.update({n:c for n,c in configs().items() if not n.startswith('FW-')})
    if a.fw:cc.update({n:firewall(n,i) for i,n in enumerate(['FW-A','FW-B'])})
    if a.acl:cc.update({n:aclclean(n) for n,_,_ in INV['groups']})
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for r in ex.map(lambda x:apply(x[0],x[1],'v2-final'),cc.items()):print(json.dumps(r,ensure_ascii=False),flush=True)
    for n,c in cc.items():(CFG/f'{n}-v2-final.txt').write_text('\n'.join(c),encoding='utf-8')
