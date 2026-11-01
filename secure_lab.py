from configure_lab import *
def fw_config(n,idx):
    c=['system-view']
    # Explicit least-privilege interzone policies. No interzone default permit.
    def policy(z1,z2,direction,num,src=None,dst=None,service=None,action='permit'):
        c.extend([f'policy interzone {z1} {z2} {direction}',f'policy {num}'])
        if src:c.append('policy source '+src)
        if dst:c.append('policy destination '+dst)
        if service:c.append('policy service service-set '+service)
        c.extend(['action '+action,'quit','quit'])
    # Internet access from hospital networks, with stateful replies.
    policy('trust','untrust','outbound',1,'10.162.0.0 0.0.255.255')
    # DMZ publishes HTTP, diagnostic ICMP is separate and explicitly limited.
    policy('dmz','untrust','inbound',1,None,'10.162.108.10 0','http')
    policy('dmz','untrust','outbound',1,'10.162.108.10 0',None,'dns')
    # Approved hospital and medical-extranet flows only.
    policy('trust','medical','outbound',1,'10.162.121.0 0.0.0.255','172.20.1.0 0.0.0.255')
    policy('trust','medical','inbound',1,'172.20.1.10 0','10.162.106.10 0','https')
    policy('trust','medical','inbound',2,'172.20.1.10 0','10.162.106.10 0','icmp')
    policy('trust','medical','inbound',3,'172.20.1.10 0','10.162.121.10 0')
    policy('trust','dmz','inbound',1,'10.162.108.10 0','10.162.106.10 0','https')
    policy('trust','dmz','outbound',1,'10.162.0.0 0.0.255.255','10.162.108.10 0','http')
    for dr in ['inbound','outbound']:
        policy('local','trust',dr,1,None,None,'ospf')
        policy('local','trust',dr,2,None,None,'icmp')
    # Pooled PAT on primary WAN; rule 2 constrained by egress interface.
    c+=['nat address-group 1 12.1.1.10 12.1.1.30','nat address-group 2 13.1.1.10 13.1.1.30',
        'nat-policy interzone trust untrust outbound','policy 1','policy source 10.162.0.0 0.0.255.255',
        'policy egress-interface GigabitEthernet0/0/0','action source-nat','address-group 1','quit',
        'policy 2','policy source 10.162.0.0 0.0.255.255','policy egress-interface GigabitEthernet0/0/1','action source-nat','address-group 2','quit','quit',
        'nat server 1 protocol tcp global 12.1.1.100 80 inside 10.162.108.10 80',
        'nat server 2 protocol tcp global 13.1.1.100 80 inside 10.162.108.10 80']
    # VRRP groups are aligned, avoiding simultaneous masters on different zones.
    for p,vip in [(0,'12.1.1.1'),(1,'13.1.1.1'),(2,'192.0.2.1'),(3,'10.162.99.1'),(4,'10.162.99.33'),(5,'10.162.108.1')]:
        c += [f'interface GigabitEthernet0/0/{p}',f'vrrp vrid {p+1} virtual-ip {vip} '+('master' if idx==0 else 'slave'),'quit']
    c += [f'hrp interface GigabitEthernet0/0/6 remote 172.31.255.{2 if idx==0 else 1}','hrp enable','return']
    return c
def agg_acls(n):
    c=['system-view'];own={int(v):d for v,d in INV['vlans'].items() if d['agg']==n}
    for v,d in own.items():
        # Server-side responses are controlled by caller ACLs and firewall state.
        if v in [60,61]:continue
        c += ['return','system-view',f'acl number {3000+v}']
        k=5
        def rule(s):
            nonlocal k
            c.append(f'rule {k} '+s);k+=5
        rule('permit udp source-port eq bootpc destination-port eq bootps')
        rule(f'permit icmp destination 10.162.{d["sub"]}.1 0')
        if v==160:
            rule('permit ip source 10.162.120.20 0')
            rule('permit ip destination 10.162.120.20 0')
            rule('deny ip destination 10.0.0.0 0.255.255.255')
        elif v==140:
            pass
        elif v in [100,110]:
            target='10.162.106.10' if v==100 else '10.162.106.11'
            rule(f'permit tcp destination {target} 0 destination-port eq '+('8883' if v==100 else '554'))
            rule(f'permit icmp destination {target} 0')
        else:
            rule('permit tcp destination 10.162.106.10 0 destination-port eq 443')
            rule('permit icmp destination 10.162.106.10 0')
            if v==50:rule('permit ip destination 172.20.1.0 0.0.0.255 source 10.162.105.20 0')
            rule('permit tcp destination 10.162.108.10 0 destination-port eq 80')
        for network,wild in [('10.0.0.0','0.255.255.255'),('172.16.0.0','0.15.255.255'),('192.168.0.0','0.0.255.255')]:rule(f'deny ip destination {network} {wild}')
        if v in [50,100,110]:rule('deny ip')
        else:rule('permit ip')
        c+=['quit',f'interface Vlanif{v}',f'traffic-filter inbound acl {3000+v}','return','system-view','ospf 1',f'silent-interface Vlanif{v}','quit']
    return c+['return']
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--fw',action='store_true');ap.add_argument('--acl',action='store_true');a=ap.parse_args()
    cc={}
    if a.fw:cc.update({n:fw_config(n,i) for i,n in enumerate(['FW-A','FW-B'])})
    if a.acl:cc.update({n:agg_acls(n) for n,_,_ in INV['groups']})
    for n,c in cc.items():(CFG/f'{n}-security.txt').write_text('\n'.join(c)+'\n',encoding='utf-8')
    # FW-A first, then FW-B: HRP configuration can synchronize automatically.
    for n,c in cc.items():print(json.dumps(apply(n,c,'security'),ensure_ascii=False),flush=True)
