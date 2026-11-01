from pathlib import Path
import json,concurrent.futures,argparse,time,socket,re
ROOT=Path(__file__).parent
INV=json.loads((ROOT/'lab_inventory.json').read_text(encoding='utf-8'))
CFG=ROOT/'output'/'医院园区网'/'配置';CFG.mkdir(parents=True,exist_ok=True)
LOG=ROOT/'evidence'/'console';LOG.mkdir(parents=True,exist_ok=True)
PROMPT=re.compile(r'(?:HRP_[MSB](?:\([^\r\n]*\))?\s*)?[<\[][A-Za-z][A-Za-z0-9_.*~:/() -]*[>\]]\s*$')
def has_prompt(t):return any(PROMPT.fullmatch(line.strip()) for line in t.splitlines()[-12:])
class Console:
    def __init__(self,port,timeout=8):self.port=port;self.timeout=timeout
    def __enter__(self):
        self.s=socket.create_connection(('127.0.0.1',self.port),self.timeout);self.s.settimeout(.2);self.s.sendall(b'\r');out=self.read()
        for _ in range(4):
            if 'file name' in out.lower() or 'filename' in out.lower():self.s.sendall(b'\r\n');out=self.read()
            elif '[y/n]' in out.lower():self.s.sendall(b'y\r\n');out=self.read()
            else:break
        return self
    def __exit__(self,*a):self.s.close()
    def read(self,timeout=None):
        out=b'';until=time.time()+(timeout or self.timeout)
        while time.time()<until:
            try:
                b=self.s.recv(65536)
                if not b:break
                out+=b
                t=out.decode('utf-8','replace').replace('\x00','')
                if re.search(r'----\s*More\s*----',t[-120:]):self.s.sendall(b' ')
                if has_prompt(t):
                    self.s.settimeout(.04)
                    try:
                        more=self.s.recv(65536)
                        if more:
                            out+=more
                            clean=out.decode('utf-8','replace').replace('\x00','')
                            if has_prompt(clean):return clean
                            continue
                    except socket.timeout:return t
                    finally:self.s.settimeout(.2)
                if '[Y/N]' in t[-120:] or '[y/n]' in t[-120:]:return t
                if re.search(r'(?:file name|filename).*\]:\s*$',t[-200:],re.I):return t
            except socket.timeout:pass
        raise TimeoutError(repr(out[-1200:]))
    def cmd(self,cmd):
        self.s.sendall(cmd.encode('ascii')+b'\r')
        if self.port in [2101,2102,2103,2133]:time.sleep(.2)
        return self.read()
def apply(n,commands,tag='config'):
    out=[]
    try:
        with Console(INV['ports'][n]) as c:
            c.cmd('return');c.cmd('screen-length 0 temporary')
            for cmd in commands:out.append(c.cmd(cmd))
    except Exception as e:out.append('EXCEPTION '+str(e))
    txt='\n'.join(out);(LOG/f'{n}-{tag}.txt').write_text(txt,encoding='utf-8')
    errors=[x.strip() for x in txt.splitlines() if any(s in x for s in ['Error:', 'Error :','Unrecognized','Incomplete command','Wrong parameter','EXCEPTION'])]
    return dict(name=n,commands=len(out),errors=errors)
def base(n):return ['system-view','undo info-center enable','sysname '+n,'stp mode mstp'] if 'SW' in n or n.startswith(('AGG-','ACC-','DC-','WAN-','BACKUP')) else ['system-view','undo info-center enable','sysname '+n]
def access(c,p,v):c.extend([f'interface GigabitEthernet0/0/{p}','port link-type access',f'port default vlan {v}','quit'])
def trunk(c,p,vs):c.extend([f'interface GigabitEthernet0/0/{p}','port link-type trunk','port trunk allow-pass vlan '+str(vs),'quit'])
def vlanif(c,v,ip,mask='255.255.255.252'):c.extend([f'interface Vlanif{v}',f'ip address {ip} {mask}','quit'])
def ospf(c,rid,areas):
    c.extend(['ospf 1 router-id '+rid])
    for area,nets in areas.items():
        c.append(f'area {area}')
        for net,wild in nets:c.append(f'network {net} {wild}')
        c.append('quit')
    c.append('quit')
def lag(c,ident,memberports,vlans):
    c.extend([f'interface Eth-Trunk{ident}','mode lacp-static','port link-type trunk','port trunk allow-pass vlan '+str(vlans),'quit'])
    for p in memberports:c.extend([f'interface GigabitEthernet0/0/{p}',f'eth-trunk {ident}','quit'])
def configs():
    allc={}
    # Shared WAN switch: three completely separate VLAN broadcast domains.
    c=base('WAN-L2')+['vlan batch 901 902 903']
    for p,v in [(1,901),(2,902),(3,903),(4,901),(5,902),(6,903),(7,901),(8,902),(9,903)]:access(c,p,v)
    allc['WAN-L2']=c+['return']
    for i in [1,2]:
        n=f'ISP-R{i}';net=11+i;c=base(n)
        c += ['interface GigabitEthernet0/0/0',f'ip address {net}.1.1.254 255.255.255.0','quit','interface GigabitEthernet0/0/1',f'ip address 203.0.{112+i}.1 255.255.255.0','quit','return']
        allc[n]=c
    c=base('HEALTH-R')
    for p,ip,mask in [(0,'192.0.2.254','255.255.255.0'),(1,'172.20.1.1','255.255.255.0'),(2,'198.18.0.1','255.255.255.252')]:c += [f'interface GigabitEthernet0/0/{p}',f'ip address {ip} {mask}','quit']
    c+=['ip route-static 10.162.106.0 24 192.0.2.1','ip route-static 10.162.121.0 24 192.0.2.1','return'];allc['HEALTH-R']=c
    for i in [1,2]:
        n=f'CORE-SW{i}';c=base(n)+['vlan batch 900 901 4094 '+ ' '.join(str(1100+i*0+j) for j in [])]
        uplinks=[(1101+j if i==1 else 1201+j) for j in range(7)]
        c+=['vlan batch '+' '.join(map(str,uplinks))]
        access(c,1,900);access(c,2,901);lag(c,1,[23,24],'900 901 4094')
        vlanif(c,900,f'10.162.99.{3+i}','255.255.255.224');vlanif(c,901,f'10.162.99.{35+i}','255.255.255.224');vlanif(c,4094,f'10.162.99.{65+i}','255.255.255.224')
        c += ['interface Vlanif4094','vrrp vrid 1 virtual-ip 10.162.99.65',f'vrrp vrid 1 priority {120 if i==1 else 100}','quit',f'stp instance 0 root {"primary" if i==1 else "secondary"}']
        nets=[('10.162.99.0','0.0.0.31'),('10.162.99.32','0.0.0.31'),('10.162.99.64','0.0.0.31')]
        for j,v in enumerate(uplinks):
            offset=(96 if i==1 else 124)+j*4
            access(c,3+j,v);vlanif(c,v,f'10.162.99.{offset+1}');nets.append((f'10.162.99.{offset}','0.0.0.3'))
            c += [f'interface GigabitEthernet0/0/{3+j}','stp disable','quit']
        ospf(c,f'10.255.255.{10+i}',{0:nets});allc[n]=c+['return']
    for gi,(n,area,acclist) in enumerate(INV['groups']):
        own={int(v):d for v,d in INV['vlans'].items() if d['agg']==n}
        c=base(n)+['dhcp enable','vlan batch '+' '.join(map(str,list(own)+[1101+gi,1201+gi]))]
        nets0=[];netsarea=[]
        for k,v in enumerate([1101+gi,1201+gi]):
            offset=(96 if k==0 else 124)+gi*4
            access(c,23+k,v);vlanif(c,v,f'10.162.99.{offset+2}');nets0.append((f'10.162.99.{offset}','0.0.0.3'))
            c += [f'interface GigabitEthernet0/0/{23+k}','stp disable','quit']
        for v,d in own.items():
            sub=d['sub'];vlanif(c,v,f'10.162.{sub}.1',d['mask'])
            c += [f'interface Vlanif{v}','dhcp select interface','dhcp server excluded-ip-address 10.162.'+str(sub)+'.2 10.162.'+str(sub)+'.49','quit']
            netsarea.append((f'10.162.{sub}.0',{'255.255.255.0':'0.0.0.255','255.255.254.0':'0.0.1.255','255.255.252.0':'0.0.3.255'}[d['mask']]))
        for j,(acc,v,sub,host) in enumerate(acclist):
            vs=f'{v} 140' if acc=='ACC-WLAN' else str(v)
            lag(c,j+1,[2*j+1,2*j+2],vs)
            a=base(acc)+['vlan batch '+vs];lag(a,1,[23,24],vs);access(a,1,v)
            a+=['interface GigabitEthernet0/0/1','stp edged-port enable','quit']
            if acc in ['ACC-WLAN','NMS-SW']:access(a,2,140 if acc=='ACC-WLAN' else 160)
            allc[acc]=a+['return']
        if n=='AGG-BRANCH':access(c,3,50);c+=['ip route-static 10.162.121.0 24 10.162.105.20']
        ospf(c,f'10.255.254.{gi+1}',{0:nets0,area:netsarea})
        if n=='AGG-BRANCH':c+=['ospf 1','import-route static','quit']
        allc[n]=c+['return']
    c=base('DMZ-SW')+['vlan 70'];access(c,1,70);access(c,23,70);access(c,24,70);allc['DMZ-SW']=c+['return']
    c=base('TELEMED-GW')
    for p,ip,mask in [(0,'10.162.105.20','255.255.255.0'),(1,'10.162.121.1','255.255.255.0'),(2,'198.18.0.2','255.255.255.252')]:c += [f'interface GigabitEthernet0/0/{p}',f'ip address {ip} {mask}','quit']
    c+=['ip route-static 0.0.0.0 0 10.162.105.1','return'];allc['TELEMED-GW']=c
    # Firewall basic IPs and dynamic routing; configure HRP after independent verification.
    for i,n in enumerate(['FW-A','FW-B']):
        c=base(n)
        for p,ip,mask in [(0,f'12.1.1.{2+i}','255.255.255.0'),(1,f'13.1.1.{2+i}','255.255.255.0'),(2,f'192.0.2.{2+i}','255.255.255.0'),(3,f'10.162.99.{2+i}','255.255.255.224'),(4,f'10.162.99.{34+i}','255.255.255.224'),(5,f'10.162.108.{2+i}','255.255.255.0'),(6,f'172.31.255.{1+i}','255.255.255.252')]:
            c += [f'interface GigabitEthernet0/0/{p}',f'ip address {ip} {mask}','undo shutdown','quit']
        for zone,ps in [('trust',[3,4]),('untrust',[0,1]),('dmz',[5])]:
            c+=['firewall zone '+zone]+[f'add interface GigabitEthernet0/0/{p}' for p in ps]+['quit']
        # USG5500 custom zone names must be <= 8 characters.
        for zone,priority,ps in [('medical',40,[2]),('ha',90,[6])]:
            c+=['firewall zone name '+zone,f'set priority {priority}']+[f'add interface GigabitEthernet0/0/{p}' for p in ps]+['quit']
        c += ['ip route-static 0.0.0.0 0.0.0.0 12.1.1.254','ip route-static 0.0.0.0 0.0.0.0 13.1.1.254 preference 100','ip route-static 172.20.1.0 24 192.0.2.254']
        ospf(c,f'10.255.255.{i+1}',{0:[('10.162.99.0','0.0.0.63'),('10.162.108.0','0.0.0.255')]})
        c+=['ospf 1','default-route-advertise','import-route static','quit','return'];allc[n]=c
    return allc
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--only',nargs='*');a=ap.parse_args()
    cc=configs()
    for n,c in cc.items():(CFG/(n+'.txt')).write_text('\n'.join(c)+'\n',encoding='utf-8')
    if a.apply:
        selected=[(n,c) for n,c in cc.items() if not a.only or n in a.only]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            for r in ex.map(lambda x:apply(*x),selected):print(json.dumps(r,ensure_ascii=False),flush=True)
